export interface Workspace {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
}

export interface Scope {
  id: number;
  workspace_id: number;
  target_type: "CIDR" | "Domain" | "IP" | "MAC";
  value: string;
  notes: string | null;
  created_at: string;
}

export interface Job {
  id: number;
  workspace_id: number;
  module: string;
  status: string;
  command_args: string;
  pgid: number | null;
  pid: number | null;
  exit_code: number | null;
  error: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface Finding {
  id: number;
  job_id: number;
  severity: string;
  title: string;
  endpoint_or_device: string | null;
  evidence: unknown | null;
  is_new_diff: boolean;
  created_at: string;
}

export interface Asset {
  id: number;
  workspace_id: number;
  asset_type: string;
  identifier: string;
  fingerprint: string;
  metadata_json: string | null;
  first_seen: string;
  last_seen: string;
}

export interface RfNetwork {
  bssid: string;
  ssid: string;
  channel: string | null;
  rssi: number;
  encryption: string | null;
  cipher: string | null;
  auth: string | null;
}

export interface RfAnalyzeOut {
  networks: RfNetwork[];
  clients: Array<Record<string, unknown>>;
  anomalies: Array<{ ssid: string; bssids: string[]; reason: string }>;
}

export interface LogEvent {
  type: string;
  job_id?: number;
  seq?: number;
  stream?: string;
  data?: string;
  ts?: number;
  status?: string;
  exit_code?: number | null;
  error?: string | null;
  events?: LogEvent[];
}
