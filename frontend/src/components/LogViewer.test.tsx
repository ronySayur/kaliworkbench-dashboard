import { describe, expect, it, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import LogViewer from "./LogViewer";

describe("LogViewer", () => {
  afterEach(() => cleanup());

  it("shows the empty-state message when no logs are present", () => {
    render(<LogViewer logs={[]} />);
    expect(screen.getByText("No log output yet.")).toBeTruthy();
  });

  it("renders stdout and stderr entries", () => {
    render(
      <LogViewer
        logs={[
          { type: "log", seq: 1, stream: "stdout", data: "hello\n" },
          { type: "log", seq: 2, stream: "stderr", data: "boom\n" },
        ]}
      />
    );
    expect(screen.getByText("hello")).toBeTruthy();
    expect(screen.getByText("boom")).toBeTruthy();
  });
});
