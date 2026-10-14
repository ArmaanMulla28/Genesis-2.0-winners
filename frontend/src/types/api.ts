export interface HealthResponse {
  status: string;
  service: string;
  active_schema_version: string;
}

export interface SchemaDetail {
  version: string;
  model_name: string;
  description: string;
  sample_payload: Record<string, any>;
  json_schema: Record<string, any>;
}

export interface SchemaInfoResponse {
  active_version: string;
  schema_name: string;
  description: string;
  expected_format: Record<string, any>;
  json_schema: Record<string, any>;
  supported_versions: string[];
  version_definitions: Record<string, SchemaDetail>;
}

export interface AuditEvent {
  event_id: string;
  attempt_id: string;
  timestamp: string;
  tool_name: string;
  endpoint: string;
  method: string;
  original_schema_version: string;
  previous_schema_version: string;
  target_schema_version: string | null;
  original_payload: Record<string, any>;
  transformed_payload: Record<string, any> | null;
  failure_reason: string;
  patch_validation_result: Record<string, any>;
  patch_decision: string;
  retry_count: number;
  max_retries: number;
  final_http_status: number;
  recovery_outcome: string;
  final_outcome: string;
  elapsed_time_ms: number;
  error_detail: string | null;
}

export interface AuditLogsResponse {
  status: string;
  total_events: number;
  limit: number;
  admin_context: string;
  events: AuditEvent[];
}

export interface MetricsResponse {
  total_recovery_attempts: number;
  successful_recoveries: number;
  failed_recoveries: number;
  eligible_recovery_attempts: number;
  adaptation_rate: number;
  mean_time_to_recovery_ms: number;
  average_retry_count: number;
  patch_rejection_count: number;
  dataset_status: string;
  notes?: string;
}

export interface ToolRegistryItem {
  tool_name: string;
  endpoint: string;
  method: string;
  active_version: string;
  last_updated: string;
  version_history: Array<{
    version?: string;
    previous_version?: string;
    timestamp: string;
    action: string;
  }>;
  schema_definition: Record<string, any>;
}

export interface RegistryResponse {
  status: string;
  registry: Record<string, ToolRegistryItem>;
}

export interface AdminActionResponse {
  status: string;
  message: string;
  previous_schema_version: string;
  active_schema_version: string;
  expected_format: Record<string, any>;
}

export interface StudentRequestResult {
  status_code: number;
  data: any;
  recovered: boolean;
  recovered_version?: string;
  duration_ms: number;
  timestamp: string;
}
