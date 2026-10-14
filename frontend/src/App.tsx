import { useCallback, useEffect, useState } from 'react';
import { Navbar } from './components/Navbar';
import { KpiOverview } from './components/KpiOverview';
import { DemoControls } from './components/DemoControls';
import { SchemaInspector } from './components/SchemaInspector';
import { AuditTable } from './components/AuditTable';
import { MetricsChart } from './components/MetricsChart';
import { api } from './services/api';
import {
  AuditEvent,
  HealthResponse,
  MetricsResponse,
  RegistryResponse,
  SchemaInfoResponse,
} from './types/api';
import { AlertCircle, ExternalLink } from 'lucide-react';

export function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [schemaInfo, setSchemaInfo] = useState<SchemaInfoResponse | null>(null);
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [registryData, setRegistryData] = useState<RegistryResponse | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const baseUrl = api.getBaseUrl();

  const loadAllData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [healthRes, schemaRes, metricsRes, auditRes, registryRes] = await Promise.all([
        api.getHealth().catch((err) => {
          console.warn('Health check failed:', err);
          return null;
        }),
        api.getSchema().catch((err) => {
          console.warn('Schema retrieval failed:', err);
          return null;
        }),
        api.getMetrics().catch((err) => {
          console.warn('Metrics calculation failed:', err);
          return null;
        }),
        api.getAuditLogs(100).catch((err) => {
          console.warn('Audit logs retrieval failed:', err);
          return null;
        }),
        api.getRegistry().catch((err) => {
          console.warn('Registry retrieval failed:', err);
          return null;
        }),
      ]);

      setHealth(healthRes);
      setSchemaInfo(schemaRes);
      setMetrics(metricsRes);
      setAuditEvents(auditRes?.events || []);
      setRegistryData(registryRes);

      if (!healthRes && !schemaRes) {
        setError(
          `Unable to connect to FastAPI backend at ${baseUrl}. Please ensure the backend server is running.`
        );
      }
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred while loading dashboard data.');
    } finally {
      setLoading(false);
    }
  }, [baseUrl]);

  useEffect(() => {
    loadAllData();
  }, [loadAllData]);

  const activeSchemaVersion = schemaInfo?.active_version || health?.active_schema_version || 'v1';

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navbar */}
      <Navbar
        health={health}
        activeSchemaVersion={activeSchemaVersion}
        loading={loading}
        onRefresh={loadAllData}
        baseUrl={baseUrl}
      />

      {/* Main Container */}
      <main className="dashboard-container" style={{ flex: 1 }}>
        {/* Global Connection Warning */}
        {error && (
          <div
            style={{
              padding: '1rem 1.25rem',
              background: 'rgba(244, 63, 94, 0.12)',
              border: '1px solid rgba(244, 63, 94, 0.3)',
              borderRadius: 8,
              color: '#fb7185',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '0.75rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <AlertCircle size={18} />
              <span style={{ fontSize: '0.85rem' }}>{error}</span>
            </div>
            <button
              onClick={loadAllData}
              className="btn btn-secondary"
              style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
            >
              Retry Connection
            </button>
          </div>
        )}

        {/* 1. KPI Overview Section */}
        <KpiOverview metrics={metrics} loading={loading} />

        {/* 2. Interactive Simulation & Demo Controls */}
        <DemoControls
          activeSchemaVersion={activeSchemaVersion}
          onStateChanged={loadAllData}
        />

        {/* 3. Metrics Timeline Chart & Schema Inspector Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(460px, 1fr))',
            gap: '1.5rem',
          }}
        >
          {/* Recovery Latency Chart */}
          <MetricsChart events={auditEvents} />

          {/* Schema Inspector */}
          <SchemaInspector
            schemaInfo={schemaInfo}
            registryData={registryData}
            loading={loading}
          />
        </div>

        {/* 4. Structured Audit Log Table */}
        <AuditTable
          events={auditEvents}
          loading={loading}
          onRefresh={loadAllData}
          error={error}
        />
      </main>

      {/* Footer */}
      <footer
        style={{
          borderTop: '1px solid var(--border-subtle)',
          padding: '1.25rem 1.5rem',
          marginTop: '2rem',
          color: 'var(--text-muted)',
          fontSize: '0.75rem',
        }}
      >
        <div
          style={{
            maxWidth: 1440,
            margin: '0 auto',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '1rem',
          }}
        >
          <div>
            <strong>Self-Healing Tool Registry</strong> — Automatic Recovery from Runtime API Schema Drift
          </div>

          <div style={{ display: 'flex', gap: '1.25rem', alignItems: 'center' }}>
            <a
              href={`${baseUrl}/docs`}
              target="_blank"
              rel="noreferrer"
              style={{ color: 'var(--accent-cyan)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
            >
              Swagger UI (/docs) <ExternalLink size={10} />
            </a>
            <a
              href={`${baseUrl}/schema`}
              target="_blank"
              rel="noreferrer"
              style={{ color: 'var(--text-secondary)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
            >
              /schema <ExternalLink size={10} />
            </a>
            <a
              href={`${baseUrl}/admin/metrics`}
              target="_blank"
              rel="noreferrer"
              style={{ color: 'var(--text-secondary)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
            >
              /admin/metrics <ExternalLink size={10} />
            </a>
            <a
              href={`${baseUrl}/admin/audit-logs`}
              target="_blank"
              rel="noreferrer"
              style={{ color: 'var(--text-secondary)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
            >
              /admin/audit-logs <ExternalLink size={10} />
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
