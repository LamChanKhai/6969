export interface FileUpload {
  id: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  extracted: boolean;
  extraction_status: string;
  security_scan_status: string;
  security_scan_result: string;
  created_at: string;
}

export interface ExtractionEvent {
  event_type: string;
  message: string;
  file_path: string;
  status: string;
  created_at: string;
}

export interface ExtractionStatus {
  upload_id: string;
  status: string;
  events: ExtractionEvent[];
  created_at: string;
}

export interface AuditLog {
  id: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  details: string;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export interface SystemHealth {
  status: string;
  version: string;
  uptime_seconds: number;
  database: string;
  storage_path: string;
  active_users: number;
  total_uploads: number;
  total_security_events: number;
}

export interface SystemMetrics {
  cpu_usage_percent: number;
  memory_usage_percent: number;
  disk_usage_percent: number;
  active_connections: number;
  requests_per_minute: number;
  avg_response_time_ms: number;
}

export interface SecurityDashboard {
  total_events: number;
  events_by_severity: Record<string, number>;
  events_last_24h: number;
  blocked_uploads: number;
  active_threats: number;
  top_vulnerabilities: Array<{ type: string; count: number }>;
}

export interface PipelineStage {
  id: string;
  stage_name: string;
  stage_order: number;
  description: string;
  is_active: boolean;
}

export interface PipelineRun {
  id: string;
  stage_name: string;
  run_number: number;
  status: string;
  started_at: string;
  finished_at: string | null;
  duration_seconds: number | null;
  logs: string;
}

export interface PipelineOverview {
  stages: PipelineStage[];
  latest_runs: PipelineRun[];
  overall_status: string;
}
