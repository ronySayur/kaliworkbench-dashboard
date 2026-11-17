import { Link, NavLink } from "react-router-dom";
import { useEffect, useState } from "react";
import { clearToken, getToken, setToken } from "../api/client";

export default function Layout({ children }: { children: React.ReactNode }) {
  const [token, setTokenState] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setTokenState(getToken());
  }, []);

  const onSave = () => {
    setToken(token);
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  };

  const onClear = () => {
    clearToken();
    setTokenState("");
  };

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-800 bg-slate-900/70">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-3 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-4">
            <Link to="/" className="text-lg font-semibold text-cyan-300">
              KaliWorkbench
            </Link>
            <nav className="flex gap-3 text-sm">
              <NavLink
                to="/"
                className={({ isActive }) =>
                  isActive ? "text-white" : "text-slate-400 hover:text-slate-200"
                }
                end
              >
                Workspaces
              </NavLink>
            </nav>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <input
              type="password"
              value={token}
              onChange={(e) => setTokenState(e.target.value)}
              placeholder="Session token (from backend startup)"
              className="w-72 rounded border border-slate-700 bg-slate-950 px-2 py-1 text-sm"
            />
            <button
              onClick={onSave}
              className="rounded bg-cyan-600 px-3 py-1 text-sm font-medium hover:bg-cyan-500"
            >
              Save
            </button>
            <button
              onClick={onClear}
              className="rounded border border-slate-700 px-3 py-1 text-sm hover:bg-slate-800"
            >
              Clear
            </button>
            {saved && <span className="text-xs text-green-400">Saved</span>}
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
    </div>
  );
}
