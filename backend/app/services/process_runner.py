from __future__ import annotations

import asyncio
import json
import os
import signal
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from app.config import settings
from app.db.engine import AsyncSessionLocal
from app.models.job import Job
from app.services.audit import write_audit_log
from app.services.ffuf import parse_ffuf_output
from app.services.gitleaks import parse_gitleaks_output
from app.services.nuclei import parse_nuclei_output
from app.services.tshark import parse_tshark_output
from app.services.ws_manager import JobStream, ws_manager
from app.models.finding import Finding


@dataclass
class RunningJob:
    job_id: int
    process: asyncio.subprocess.Process
    task: asyncio.Task[None]
    cancel_requested: bool = False


class ProcessRunner:
    def __init__(self) -> None:
        self._running: dict[int, RunningJob] = {}
        self._semaphore = asyncio.Semaphore(settings.max_concurrent_jobs)

    def is_running(self, job_id: int) -> bool:
        return job_id in self._running

    async def start_job(self, job_id: int, command: list[str], timeout: int) -> None:
        task = asyncio.create_task(self._run_job(job_id, command, timeout))
        if not hasattr(self, "_tasks"):
            self._tasks: set[asyncio.Task[None]] = set()
        self._tasks.add(task)
        task.add_done_callback(lambda t: self._tasks.discard(t))

    async def cancel_job(self, job_id: int) -> bool:
        running = self._running.get(job_id)
        if not running:
            return False
        running.cancel_requested = True
        await self._terminate_group(running.process, graceful=True)
        asyncio.create_task(self._ensure_killed(running.process))
        return True

    async def _ensure_killed(self, process: asyncio.subprocess.Process) -> None:
        if process.returncode is not None:
            return
        try:
            await asyncio.wait_for(process.wait(), timeout=settings.job_cancel_grace_seconds)
        except asyncio.TimeoutError:
            await self._terminate_group(process, graceful=False)
            try:
                await asyncio.wait_for(process.wait(), timeout=2)
            except Exception:
                pass
        except Exception:
            pass

    async def _terminate_group(self, process: asyncio.subprocess.Process, graceful: bool) -> None:
        pid = process.pid
        if pid is None:
            return
        try:
            pgid = os.getpgid(pid)
        except ProcessLookupError:
            return
        try:
            if graceful:
                os.killpg(pgid, signal.SIGTERM)
            else:
                os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            return
        except PermissionError:
            try:
                process.terminate() if graceful else process.kill()
            except ProcessLookupError:
                pass

    async def _run_job(self, job_id: int, command: list[str], timeout: int) -> None:
        stream = await ws_manager.get_or_create(job_id)
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Job).where(Job.id == job_id))
            job = result.scalar_one_or_none()
            if not job or job.status == "cancelled":
                stream.queue_event({"type": "status", "status": "cancelled", "error": "cancelled before start"})
                await stream.flush()
                return
        async with self._semaphore:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(Job).where(Job.id == job_id))
                job = result.scalar_one_or_none()
                if not job or job.status == "cancelled":
                    stream.queue_event({"type": "status", "status": "cancelled", "error": "cancelled before start"})
                    await stream.flush()
                    return
            now = datetime.now(timezone.utc)
            await self._update_job(job_id, status="running", started_at=now, error=None)
            stream.queue_event({"type": "status", "status": "running"})
            process: asyncio.subprocess.Process | None = None
            timed_out = False
            cancelled = False
            try:
                process = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    start_new_session=True,
                )
                running = RunningJob(job_id=job_id, process=process, task=asyncio.current_task())  # type: ignore[arg-type]
                self._running[job_id] = running
                pgid = None
                try:
                    pgid = os.getpgid(process.pid)
                except Exception:
                    pgid = None
                await self._update_job(job_id, pid=process.pid, pgid=pgid)
                stream.queue_event({"type": "meta", "pid": process.pid, "pgid": pgid})

                stdout_task = asyncio.create_task(self._read_stream(process.stdout, "stdout", stream))
                stderr_task = asyncio.create_task(self._read_stream(process.stderr, "stderr", stream))
                wait_task = asyncio.create_task(process.wait())
                try:
                    await asyncio.wait_for(wait_task, timeout=timeout)
                except asyncio.TimeoutError:
                    timed_out = True
                    await self._terminate_group(process, graceful=True)
                    try:
                        await asyncio.wait_for(process.wait(), timeout=settings.job_cancel_grace_seconds)
                    except asyncio.TimeoutError:
                        await self._terminate_group(process, graceful=False)
                        await process.wait()
                await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)

                running = self._running.get(job_id)
                if running and running.cancel_requested and not timed_out:
                    cancelled = True
            except FileNotFoundError as e:
                stream.append_log("stderr", f"command not found: {command[0]}\n")
                await self._finalize(job_id, stream, status="failed", exit_code=127, error=str(e))
                return
            except Exception as e:
                stream.append_log("stderr", f"runner error: {e}\n")
                await self._finalize(job_id, stream, status="failed", exit_code=None, error=str(e))
                return
            finally:
                self._running.pop(job_id, None)

            exit_code = process.returncode if process else None
            if timed_out:
                await self._finalize(job_id, stream, status="timed_out", exit_code=exit_code, error="timeout")
            elif cancelled:
                await self._finalize(job_id, stream, status="cancelled", exit_code=exit_code, error="cancelled")
            elif exit_code == 0:
                await self._finalize(job_id, stream, status="succeeded", exit_code=exit_code, error=None)
            else:
                await self._finalize(job_id, stream, status="failed", exit_code=exit_code, error=f"exit {exit_code}")

    async def _read_stream(self, reader: asyncio.StreamReader | None, name: str, stream: JobStream) -> None:
        if reader is None:
            return
        while True:
            chunk = await reader.read(4096)
            if not chunk:
                break
            text = chunk.decode("utf-8", errors="replace")
            stream.append_log(name, text)

    async def _finalize(
        self,
        job_id: int,
        stream: JobStream,
        *,
        status: str,
        exit_code: int | None,
        error: str | None,
    ) -> None:
        finished = datetime.now(timezone.utc)
        await self._update_job(job_id, status=status, exit_code=exit_code, error=error, finished_at=finished)
        stream.queue_event({"type": "status", "status": status, "exit_code": exit_code, "error": error})
        await stream.flush()
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Job).where(Job.id == job_id))
            job = result.scalar_one_or_none()
            if job and status == "succeeded" and job.module == "gitleaks":
                output_text = "".join(entry.data or "" for entry in stream.buffer.snapshot())
                parsed_findings = parse_gitleaks_output(output_text)
                for pf in parsed_findings:
                    session.add(
                        Finding(
                            job_id=job.id,
                            severity=pf.get("severity") or "UNKNOWN",
                            title=pf.get("title") or "Secret detected",
                            endpoint_or_device=None,
                            evidence_json=json.dumps(pf.get("evidence") or {}, ensure_ascii=False),
                            is_new_diff=False,
                        )
                    )
            if job and status == "succeeded" and job.module == "ffuf":
                output_text = "".join(entry.data or "" for entry in stream.buffer.snapshot())
                parsed_findings = parse_ffuf_output(output_text)
                for pf in parsed_findings:
                    session.add(
                        Finding(
                            job_id=job.id,
                            severity=pf.get("severity") or "INFO",
                            title=pf.get("title") or "Fuzz result",
                            endpoint_or_device=None,
                            evidence_json=json.dumps(pf.get("evidence") or {}, ensure_ascii=False),
                            is_new_diff=False,
                        )
                    )
            if job and status == "succeeded" and job.module == "nuclei":
                output_text = "".join(entry.data or "" for entry in stream.buffer.snapshot())
                parsed_findings = parse_nuclei_output(output_text)
                for pf in parsed_findings:
                    session.add(
                        Finding(
                            job_id=job.id,
                            severity=pf.get("severity") or "UNKNOWN",
                            title=pf.get("title") or "Vulnerability detected",
                            endpoint_or_device=None,
                            evidence_json=json.dumps(pf.get("evidence") or {}, ensure_ascii=False),
                            is_new_diff=False,
                        )
                    )
            if job and status == "succeeded" and job.module == "tshark":
                output_text = "".join(entry.data or "" for entry in stream.buffer.snapshot())
                parsed_findings = parse_tshark_output(output_text)
                for pf in parsed_findings:
                    session.add(
                        Finding(
                            job_id=job.id,
                            severity=pf.get("severity") or "MEDIUM",
                            title=pf.get("title") or "Packet inspection finding",
                            endpoint_or_device=None,
                            evidence_json=json.dumps(pf.get("evidence") or {}, ensure_ascii=False),
                            is_new_diff=False,
                        )
                    )
            if job:
                await write_audit_log(
                    session,
                    workspace_id=job.workspace_id,
                    job_id=job.id,
                    module=job.module,
                    action="execute",
                    status=status,
                    command_args=job.command_args,
                )
                await session.commit()

    async def _update_job(self, job_id: int, **fields: Any) -> None:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Job).where(Job.id == job_id))
            job = result.scalar_one_or_none()
            if not job:
                return
            for k, v in fields.items():
                setattr(job, k, v)
            await session.commit()


process_runner = ProcessRunner()
