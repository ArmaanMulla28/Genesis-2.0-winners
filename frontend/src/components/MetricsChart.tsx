import React from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { BarChart3, LineChart } from 'lucide-react';
import { AuditEvent } from '../types/api';

interface MetricsChartProps {
  events: AuditEvent[];
}

export const MetricsChart: React.FC<MetricsChartProps> = ({ events }) => {
  // Sort oldest to newest, take last 15
  const chartData = [...events]
    .slice(-15)
    .map((e, index) => ({
      index: index + 1,
      name: `#${index + 1} (${e.previous_schema_version || 'v1'}>${e.target_schema_version || 'v2'})`,
      duration: e.elapsed_time_ms,
      outcome: e.recovery_outcome || e.final_outcome,
      time: new Date(e.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    }));

  if (chartData.length === 0) {
    return (
      <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        <div className="card-header" style={{ margin: 0, paddingBottom: '0.5rem' }}>
          <div className="card-title">
            <LineChart size={18} color="var(--accent-amber)" />
            <span>Recovery Latency Timeline (MTTR in ms)</span>
          </div>
        </div>
        <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
          No recovery latency data available yet. Execute recovery attempts to view latency distribution.
        </div>
      </div>
    );
  }

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div className="card-header" style={{ margin: 0, paddingBottom: '0.75rem' }}>
        <div className="card-title">
          <BarChart3 size={18} color="var(--accent-amber)" />
          <span>Recovery Latency Timeline (MTTR in ms, Last {chartData.length} Attempts)</span>
        </div>
        <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#34d399' }}></span>
            Success (200 OK)
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#fb7185' }}></span>
            Rejected / Failed (422)
          </span>
        </div>
      </div>

      <div style={{ width: '100%', height: 220 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 15, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis
              dataKey="name"
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
            />
            <YAxis
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              unit="ms"
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div
                      style={{
                        background: '#0f172a',
                        border: '1px solid #334155',
                        padding: '0.5rem 0.75rem',
                        borderRadius: 6,
                        fontSize: '0.75rem',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
                      }}
                    >
                      <div style={{ fontWeight: 600, color: '#f8fafc', marginBottom: 2 }}>
                        Attempt {data.name}
                      </div>
                      <div style={{ color: '#94a3b8' }}>
                        Time: <span style={{ color: '#cbd5e1' }}>{data.time}</span>
                      </div>
                      <div style={{ color: '#94a3b8' }}>
                        Duration: <strong style={{ color: '#38bdf8' }}>{data.duration} ms</strong>
                      </div>
                      <div style={{ color: '#94a3b8' }}>
                        Outcome: <span style={{ color: data.outcome === 'SUCCESS' ? '#34d399' : '#fb7185' }}>{data.outcome}</span>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Bar dataKey="duration" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.outcome === 'SUCCESS' ? '#10b981' : '#f43f5e'}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
