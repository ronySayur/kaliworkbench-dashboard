export interface ResponseDiffOut {
  same: boolean;
  differences: Array<{
    path: string;
    status: string;
    value?: unknown;
    source_value?: unknown;
    target_value?: unknown;
  }>;
  error: string | null;
  source: string | null;
  target: string | null;
}
