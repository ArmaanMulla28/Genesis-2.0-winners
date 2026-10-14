import React, { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  RotateCcw,
  Send,
  Sparkles,
  Zap,
} from 'lucide-react';
import { api } from '../services/api';
import { StudentRequestResult } from '../types/api';

interface DemoControlsProps {
  activeSchemaVersion: string;
  onStateChanged: () => void;
}

export const DemoControls: React.FC<DemoControlsProps> = ({
  activeSchemaVersion,
  onStateChanged,
}) => {
  const [payloadText, setPayloadText] = useState('{\n  "user_id": "123"\n}');
  const [bypassRecovery, setBypassRecovery] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<StudentRequestResult | null>(null);
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error' | 'warning' | 'info'; text: string } | null>(null);

  const presets = [
    {
      label: 'Schema v1 (Original)',
      value: '{\n  "user_id": "123"\n}',
      desc: 'Old format: string user_id',
    },
    {
      label: 'Schema v2 (Drifted)',
      value: '{\n  "target": {\n    "id": 123\n  }\n}',
      desc: 'New format: nested target.id integer',
    },
    {
      label: 'Incompatible (Non-Numeric)',
      value: '{\n  "user_id": "cannot_convert_to_int"\n}',
      desc: 'Non-numeric string fails v2 conversion',
    },
    {
      label: 'Security Injection',
      value: '{\n  "user_id": "123",\n  "bearer_token": "secret_abc"\n}',
      desc: 'Unauthorized credential rejected',
    },
  ];

  const handleBreakApi = async () => {
    setActionLoading('break');
    setStatusMessage(null);
    try {
      const res = await api.breakApi();
      setStatusMessage({
        type: 'warning',
        text: `Schema Drift Simulated: API switched to ${res.active_schema_version}. Expected format: ${JSON.stringify(res.expected_format)}`,
      });
      onStateChanged();
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: `Failed to break API: ${err.message}` });
    } finally {
      setActionLoading(null);
    }
  };

  const handleResetApi = async () => {
    setActionLoading('reset');
    setStatusMessage(null);
    try {
      const res = await api.resetApi();
      setStatusMessage({
        type: 'success',
        text: `API Reset: Restored to original schema ${res.active_schema_version}. Audit log and metrics cleared.`,
      });
      setLastResult(null);
      onStateChanged();
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: `Failed to reset API: ${err.message}` });
    } finally {
      setActionLoading(null);
    }
  };

  const handleSendRequest = async () => {
    setSubmitting(true);
    setStatusMessage(null);
    try {
      let parsedPayload: any;
      try {
        parsedPayload = JSON.parse(payloadText);
      } catch {
        parsedPayload = payloadText;
      }

      const result = await api.submitStudent(parsedPayload, bypassRecovery);
      setLastResult(result);
      onStateChanged();
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: `Execution failed: ${err.message}` });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div className="card-header" style={{ margin: 0, paddingBottom: '0.75rem' }}>
        <div className="card-title">
          <Zap size={18} color="var(--accent-cyan)" />
          <span>Interactive Simulation & Recovery Sandbox</span>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={handleBreakApi}
            disabled={actionLoading !== null || activeSchemaVersion === 'v2'}
            className="btn btn-secondary"
            style={{ color: '#fb7185', borderColor: 'rgba(244, 63, 94, 0.3)' }}
            title="Simulates runtime API drift by switching active schema to v2"
          >
            <AlertTriangle size={14} />
            <span>{actionLoading === 'break' ? 'Simulating...' : 'Simulate Drift (/admin/break-api)'}</span>
          </button>

          <button
            onClick={handleResetApi}
            disabled={actionLoading !== null}
            className="btn btn-secondary"
            title="Restores API and Tool Registry back to initial v1 schema"
          >
            <RotateCcw size={14} />
            <span>{actionLoading === 'reset' ? 'Resetting...' : 'Reset API (/admin/reset-api)'}</span>
          </button>
        </div>
      </div>

      {/* Confirmation / Status Banner */}
      {statusMessage && (
        <div
          style={{
            padding: '0.75rem 1rem',
            borderRadius: 6,
            fontSize: '0.825rem',
            background:
              statusMessage.type === 'success'
                ? 'rgba(16, 185, 129, 0.1)'
                : statusMessage.type === 'warning'
                ? 'rgba(245, 158, 11, 0.1)'
                : 'rgba(244, 63, 94, 0.1)',
            border: `1px solid ${
              statusMessage.type === 'success'
                ? 'rgba(16, 185, 129, 0.3)'
                : statusMessage.type === 'warning'
                ? 'rgba(245, 158, 11, 0.3)'
                : 'rgba(244, 63, 94, 0.3)'
            }`,
            color:
              statusMessage.type === 'success'
                ? '#34d399'
                : statusMessage.type === 'warning'
                ? '#fbbf24'
                : '#fb7185',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          {statusMessage.type === 'success' ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
          <span>{statusMessage.text}</span>
        </div>
      )}

      {/* Request Sandbox Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '1.25rem',
        }}
      >
        {/* Left Column: Request Composer */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
              POST /student Request Payload
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Server expects: <strong>{activeSchemaVersion}</strong>
            </span>
          </div>

          {/* Preset Buttons */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
            {presets.map((p) => (
              <button
                key={p.label}
                onClick={() => setPayloadText(p.value)}
                className="btn btn-secondary"
                style={{ fontSize: '0.725rem', padding: '0.3rem 0.55rem' }}
                title={p.desc}
              >
                {p.label}
              </button>
            ))}
          </div>

          <textarea
            value={payloadText}
            onChange={(e) => setPayloadText(e.target.value)}
            rows={7}
            className="form-textarea"
            placeholder="Enter JSON payload..."
            style={{ resize: 'vertical' }}
          />

          {/* Options & Send Button */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              <input
                type="checkbox"
                checked={bypassRecovery}
                onChange={(e) => setBypassRecovery(e.target.checked)}
                style={{ accentColor: '#38bdf8' }}
              />
              <span>Bypass Self-Healing (receive raw HTTP 422)</span>
            </label>

            <button
              onClick={handleSendRequest}
              disabled={submitting}
              className="btn btn-primary"
            >
              <Send size={14} />
              <span>{submitting ? 'Executing...' : 'Send Request'}</span>
            </button>
          </div>
        </div>

        {/* Right Column: Response Inspector */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
              Response Inspector
            </span>
            {lastResult && (
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  {lastResult.duration_ms} ms
                </span>
                <span
                  className={`badge ${
                    lastResult.status_code === 200
                      ? 'badge-success'
                      : lastResult.status_code === 422
                      ? 'badge-danger'
                      : 'badge-warning'
                  }`}
                >
                  HTTP {lastResult.status_code}
                </span>
              </div>
            )}
          </div>

          {lastResult?.recovered && (
            <div
              style={{
                background: 'rgba(56, 189, 248, 0.1)',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                padding: '0.5rem 0.75rem',
                borderRadius: 6,
                fontSize: '0.775rem',
                color: '#38bdf8',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
              }}
            >
              <Sparkles size={14} />
              <span>
                <strong>Self-Healing Engaged:</strong> Payload was automatically adapted and retried successfully under schema <strong>{lastResult.recovered_version || 'v2'}</strong>!
              </span>
            </div>
          )}

          <div
            className="json-box"
            style={{
              minHeight: 180,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: lastResult ? 'flex-start' : 'center',
              alignItems: lastResult ? 'stretch' : 'center',
            }}
          >
            {lastResult ? (
              <pre style={{ margin: 0 }}>
                {JSON.stringify(lastResult.data, null, 2)}
              </pre>
            ) : (
              <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                Click "Send Request" to observe real-time validation and self-healing recovery.
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
