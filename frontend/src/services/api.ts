import {
  AdminActionResponse,
  AuditLogsResponse,
  HealthResponse,
  MetricsResponse,
  RegistryResponse,
  SchemaInfoResponse,
  StudentRequestResult,
} from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL.replace(/\/+$/, '');
  }

  getBaseUrl(): string {
    return this.baseUrl;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        let errorData: any;
        try {
          errorData = await response.json();
        } catch {
          errorData = { detail: response.statusText };
        }
        const error: any = new Error(
          typeof errorData.detail === 'string'
            ? errorData.detail
            : JSON.stringify(errorData.detail || errorData)
        );
        error.status = response.status;
        error.data = errorData;
        throw error;
      }

      return await response.json();
    } catch (err: any) {
      if (err.name === 'TypeError' && err.message.includes('fetch')) {
        throw new Error(
          `Unable to connect to backend server at ${this.baseUrl}. Please verify the FastAPI server is running.`
        );
      }
      throw err;
    }
  }

  async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  async getSchema(): Promise<SchemaInfoResponse> {
    return this.request<SchemaInfoResponse>('/schema');
  }

  async getMetrics(): Promise<MetricsResponse> {
    return this.request<MetricsResponse>('/admin/metrics');
  }

  async getAuditLogs(limit: number = 50): Promise<AuditLogsResponse> {
    return this.request<AuditLogsResponse>(`/admin/audit-logs?limit=${limit}`);
  }

  async getRegistry(): Promise<RegistryResponse> {
    return this.request<RegistryResponse>('/registry');
  }

  async breakApi(): Promise<AdminActionResponse> {
    return this.request<AdminActionResponse>('/admin/break-api', {
      method: 'POST',
    });
  }

  async resetApi(): Promise<AdminActionResponse> {
    return this.request<AdminActionResponse>('/admin/reset-api', {
      method: 'POST',
    });
  }

  async clearAudit(): Promise<{ status: string; message: string }> {
    return this.request<{ status: string; message: string }>('/audit', {
      method: 'DELETE',
    });
  }

  async submitStudent(payload: any, bypassRecovery: boolean = false): Promise<StudentRequestResult> {
    const url = `${this.baseUrl}/student${bypassRecovery ? '?bypass_recovery=true' : ''}`;
    const startTime = performance.now();

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(bypassRecovery ? { 'X-Bypass-Recovery': 'true' } : {}),
        },
        body: typeof payload === 'string' ? payload : JSON.stringify(payload),
      });

      const durationMs = Math.round((performance.now() - startTime) * 10) / 10;
      const recovered = response.headers.get('x-self-healing-recovered') === 'true';
      const recoveredVersion = response.headers.get('x-self-healing-version') || undefined;

      let responseData: any;
      try {
        responseData = await response.json();
      } catch {
        responseData = { message: response.statusText };
      }

      return {
        status_code: response.status,
        data: responseData,
        recovered,
        recovered_version: recoveredVersion,
        duration_ms: durationMs,
        timestamp: new Date().toISOString(),
      };
    } catch (err: any) {
      const durationMs = Math.round((performance.now() - startTime) * 10) / 10;
      return {
        status_code: 0,
        data: { error: err.message || 'Connection failed' },
        recovered: false,
        duration_ms: durationMs,
        timestamp: new Date().toISOString(),
      };
    }
  }
}

export const api = new ApiService();
