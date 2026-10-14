import React, { useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  History,
  RefreshCw,
  Search,
  ShieldCheck,
  XCircle,
} from 'lucide-react';
import { AuditEvent } from '../types/api';

interface AuditTableProps {
  events: AuditEvent[];
  loading: boolean;
  onRefresh: () => void;
  error?: string | null;
}

export const AuditTable: React.FC<AuditTableProps> = ({
  events,
  loading,
  onRefresh,
  error,
}) => {
  const [filterText, setFilterText] = useState('');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filteredEvents = events.filter((e) => {
    if (!filterText) return true;
    const q = filterText.toLowerCase();
    return (
      e.tool_name.toLowerCase().includes(q) ||
      e.endpoint.toLowerCase().includes(q) ||
      e.recovery_outcome.toLowerCase().includes(q) ||
      e.patch_decision.toLowerCase().includes(q) ||
      e.event_id.toLowerCase().includes(q)
    );
  });

  const getOutcomeBadge = (outcome: string) => {
    switch (outcome) {
      case 'SUCCESS':
        return <span className="badge badge-success"><CheckCircle2 size={10} /> SUCCESS</span>;
      case 'REJECTED':
        return <span className="badge badge-warning"><AlertCircle size={10} /> REJECTED</span>;
      case 'RETRY_LIMIT_EXCEEDED':
      case 'FAILED':
        return <span className="badge badge-danger"><XCircle size={10} /> FAILED</span>;
      default:
        return <span className="badge badge-neutral">{outcome}</span>;
    }
  };

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div className="card-header" style={{ margin: 0, paddingBottom: '0.75rem' }}>
        <div className="card-title">
          <History size={18} color="var(--accent-blue)" />
          <span>Recovery Activity Audit Trail (/admin/audit-logs)</span>
          <span className="badge badge-neutral" style={{ fontWeight: 400 }}>
            {events.length} records
          </span>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          {/* Search Filter */}
          <div style={{ position: 'relative', width: 220 }}>
            <Search
              size={12}
              style={{
                position: 'absolute',
                left: 8,
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--text-muted)',
              }}
            />
            <input
              type="text"
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              placeholder="Search audit trail..."
              className="form-input"
              style={{ paddingLeft: '1.75rem', fontSize: '0.775rem', height: 30 }}
            />
          </div>

          <button
            onClick={onRefresh}
            disabled={loading}
            className="btn btn-secondary"
            style={{ padding: '0.3rem 0.65rem', fontSize: '0.75rem' }}
            title="Refresh audit events"
          >
            <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div
          style={{
            padding: '1rem',
            background: 'rgba(244, 63, 94, 0.1)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            color: '#fb7185',
            borderRadius: 6,
            fontSize: '0.825rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <AlertCircle size={16} />
          <span>Failed to load audit logs: {error}</span>
        </div>
      )}

      {/* Loading state */}
      {loading && events.length === 0 && (
        <div style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading structured audit records...
        </div>
      )}

      {/* Empty state */}
      {!loading && events.length === 0 && !error && (
        <div
          style={{
            padding: '2.5rem',
            textAlign: 'center',
            color: 'var(--text-muted)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <ShieldCheck size={32} color="var(--border-strong)" />
          <span style={{ fontSize: '0.85rem' }}>No recovery events recorded yet.</span>
          <span style={{ fontSize: '0.75rem' }}>
            Simulate schema drift with the controls above and send an outdated request to trigger self-healing.
          </span>
        </div>
      )}

      {/* Table Content */}
      {events.length > 0 && (
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: 30 }}></th>
                <th>Timestamp (UTC)</th>
                <th>Tool / Endpoint</th>
                <th>Schema Drift</th>
                <th>Patch Decision</th>
                <th>Retries</th>
                <th>Outcome</th>
                <th>MTTR</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredEvents.map((event) => {
                const isExpanded = expandedId === event.event_id;
                const formattedTime = new Date(event.timestamp).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                  second: '2-digit',
                  hour12: false,
                });

                return (
                  <React.Fragment key={event.event_id}>
                    <tr
                      onClick={() => toggleExpand(event.event_id)}
                      style={{ cursor: 'pointer', background: isExpanded ? 'rgba(56, 189, 248, 0.05)' : undefined }}
                    >
                      <td>
                        {isExpanded ? (
                          <ChevronDown size={14} color="var(--accent-cyan)" />
                        ) : (
                          <ChevronRight size={14} color="var(--text-muted)" />
                        )}
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.775rem' }}>
                        {formattedTime}
                      </td>
                      <td>
                        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                          {event.method} {event.endpoint}
                        </span>
                        <span style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                          {event.tool_name}
                        </span>
                      </td>
                      <td>
                        <span className="badge badge-neutral" style={{ fontSize: '0.7rem' }}>
                          {event.original_schema_version || event.previous_schema_version} &rarr; {event.target_schema_version || 'unknown'}
                        </span>
                      </td>
                      <td style={{ maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        <span title={event.patch_decision} style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
                          {event.patch_decision}
                        </span>
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>
                        {event.retry_count}/{event.max_retries}
                      </td>
                      <td>{getOutcomeBadge(event.recovery_outcome || event.final_outcome)}</td>
                      <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-amber)' }}>
                        {event.elapsed_time_ms} ms
                      </td>
                      <td>
                        <span
                          className={`badge ${
                            event.final_http_status === 200
                              ? 'badge-success'
                              : 'badge-danger'
                          }`}
                        >
                          {event.final_http_status}
                        </span>
                      </td>
                    </tr>

                    {/* Expanded Payload & Details Viewer */}
                    {isExpanded && (
                      <tr style={{ background: 'rgba(15, 23, 42, 0.5)' }}>
                        <td colSpan={9} style={{ padding: '1rem 1.5rem' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                                Event UUID: {event.event_id} | Failure Reason: <code>{event.failure_reason}</code>
                              </span>
                              {event.error_detail && (
                                <span style={{ fontSize: '0.75rem', color: '#fb7185' }}>
                                  Detail: {event.error_detail}
                                </span>
                              )}
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
                              {/* Original Payload */}
                              <div>
                                <span style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem' }}>
                                  Original Payload (Sanitized)
                                </span>
                                <div className="json-box" style={{ maxHeight: 160 }}>
                                  <pre style={{ margin: 0 }}>
                                    {JSON.stringify(event.original_payload, null, 2)}
                                  </pre>
                                </div>
                              </div>

                              {/* Transformed Payload */}
                              <div>
                                <span style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem' }}>
                                  Transformed Payload (Target Schema)
                                </span>
                                <div className="json-box" style={{ maxHeight: 160 }}>
                                  <pre style={{ margin: 0 }}>
                                    {event.transformed_payload
                                      ? JSON.stringify(event.transformed_payload, null, 2)
                                      : '// No transformation generated (rejected or failed)'}
                                  </pre>
                                </div>
                              </div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
