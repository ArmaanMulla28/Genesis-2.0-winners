import React from 'react';
import { Activity, CheckCircle2, Clock, XCircle } from 'lucide-react';
import { MetricsResponse } from '../types/api';

interface KpiOverviewProps {
  metrics: MetricsResponse | null;
  loading: boolean;
}

export const KpiOverview: React.FC<KpiOverviewProps> = ({ metrics, loading }) => {
  const attempts = metrics?.total_recovery_attempts ?? 0;
  const successful = metrics?.successful_recoveries ?? 0;
  const failed = metrics?.failed_recoveries ?? 0;
  const adaptationRate = metrics?.adaptation_rate ?? 0;
  const mttr = metrics?.mean_time_to_recovery_ms ?? 0;
  const avgRetries = metrics?.average_retry_count ?? 0;
  const patchRejections = metrics?.patch_rejection_count ?? 0;

  const getAdaptationBadge = (rate: number, total: number) => {
    if (total === 0) return 'badge-neutral';
    if (rate >= 90) return 'badge-success';
    if (rate >= 50) return 'badge-warning';
    return 'badge-danger';
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
        <h2 style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          System Recovery KPIs (/admin/metrics)
        </h2>
        {metrics?.dataset_status === 'empty' && (
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Baseline active: No schema recovery attempts recorded yet.
          </span>
        )}
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '1rem',
        }}
      >
        {/* KPI 1: Total Attempts */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: 'var(--text-muted)' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 500 }}>Total Recovery Attempts</span>
            <Activity size={16} color="var(--accent-cyan)" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
            {loading ? '...' : attempts}
          </div>
          <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>
            Triggered by runtime HTTP 422 drift
          </div>
        </div>

        {/* KPI 2: Successful Recoveries */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: 'var(--text-muted)' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 500 }}>Successful Recoveries</span>
            <CheckCircle2 size={16} color="var(--accent-emerald)" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#34d399', fontFamily: 'var(--font-mono)' }}>
            {loading ? '...' : successful}
          </div>
          <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>
            Transparently healed to 200 OK
          </div>
        </div>

        {/* KPI 3: Failed Recoveries */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: 'var(--text-muted)' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 500 }}>Failed / Rejected</span>
            <XCircle size={16} color="var(--accent-rose)" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: failed > 0 ? '#fb7185' : 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
            {loading ? '...' : failed}
          </div>
          <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>
            {patchRejections} rejected patches
          </div>
        </div>

        {/* KPI 4: Adaptation Rate */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: 'var(--text-muted)' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 500 }}>Adaptation Rate</span>
            <div className={`badge ${getAdaptationBadge(adaptationRate, attempts)}`}>
              {adaptationRate}%
            </div>
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
            {loading ? '...' : `${adaptationRate}%`}
          </div>
          <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>
            Successes / Eligible attempts
          </div>
        </div>

        {/* KPI 5: MTTR */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: 'var(--text-muted)' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 500 }}>Mean Time to Recovery (MTTR)</span>
            <Clock size={16} color="var(--accent-amber)" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#fbbf24', fontFamily: 'var(--font-mono)' }}>
            {loading ? '...' : `${mttr} ms`}
          </div>
          <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>
            Avg retries: {avgRetries} (Max 1)
          </div>
        </div>
      </div>
    </div>
  );
};
