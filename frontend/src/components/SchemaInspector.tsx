import React, { useState } from 'react';
import { BookOpen, GitCompare, Layers, ShieldCheck } from 'lucide-react';
import { RegistryResponse, SchemaInfoResponse } from '../types/api';

interface SchemaInspectorProps {
  schemaInfo: SchemaInfoResponse | null;
  registryData: RegistryResponse | null;
  loading: boolean;
}

export const SchemaInspector: React.FC<SchemaInspectorProps> = ({
  schemaInfo,
  registryData,
  loading,
}) => {
  const [activeTab, setActiveTab] = useState<'comparison' | 'active_schema' | 'tool_registry'>('comparison');

  const v1Def = schemaInfo?.version_definitions?.v1;
  const v2Def = schemaInfo?.version_definitions?.v2;

  const studentTool = registryData?.registry?.student_service;

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div className="card-header" style={{ margin: 0, paddingBottom: '0.75rem' }}>
        <div className="card-title">
          <BookOpen size={18} color="var(--accent-purple)" />
          <span>Schema Contract Inspector (/schema & /registry)</span>
        </div>

        {/* Tab Selector */}
        <div style={{ display: 'flex', gap: '0.35rem' }}>
          <button
            onClick={() => setActiveTab('comparison')}
            className={`btn ${activeTab === 'comparison' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.75rem', padding: '0.3rem 0.65rem' }}
          >
            <GitCompare size={12} />
            <span>Before & After Drift</span>
          </button>

          <button
            onClick={() => setActiveTab('active_schema')}
            className={`btn ${activeTab === 'active_schema' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.75rem', padding: '0.3rem 0.65rem' }}
          >
            <ShieldCheck size={12} />
            <span>Current Active ({schemaInfo?.active_version || 'v1'})</span>
          </button>

          <button
            onClick={() => setActiveTab('tool_registry')}
            className={`btn ${activeTab === 'tool_registry' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.75rem', padding: '0.3rem 0.65rem' }}
          >
            <Layers size={12} />
            <span>Tool Registry</span>
          </button>
        </div>
      </div>

      {loading && !schemaInfo ? (
        <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading schema specifications...
        </div>
      ) : activeTab === 'comparison' ? (
        /* Side by Side Comparison */
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1rem' }}>
          {/* Schema v1 Column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <span className="badge badge-info">v1.0 (Baseline)</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {v1Def?.model_name || 'StudentRequestV1'}
                </span>
              </div>
              {schemaInfo?.active_version === 'v1' && (
                <span className="badge badge-success">Currently Active</span>
              )}
            </div>

            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {v1Def?.description || "Original schema: expects top-level string field 'user_id'"}
            </p>

            <span style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
              Sample Valid Payload
            </span>
            <div className="json-box" style={{ maxHeight: 110 }}>
              <pre style={{ margin: 0 }}>
                {JSON.stringify(v1Def?.sample_payload || { user_id: '123' }, null, 2)}
              </pre>
            </div>

            <span style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
              OpenAPI JSON Schema
            </span>
            <div className="json-box" style={{ maxHeight: 180 }}>
              <pre style={{ margin: 0 }}>
                {JSON.stringify(v1Def?.json_schema || {}, null, 2)}
              </pre>
            </div>
          </div>

          {/* Schema v2 Column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <span className="badge badge-warning">v2.0 (Drifted)</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {v2Def?.model_name || 'StudentRequestV2'}
                </span>
              </div>
              {schemaInfo?.active_version === 'v2' && (
                <span className="badge badge-success">Currently Active</span>
              )}
            </div>

            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {v2Def?.description || "Changed schema (drifted): expects nested 'target' object with integer 'id'"}
            </p>

            <span style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
              Sample Valid Payload
            </span>
            <div className="json-box" style={{ maxHeight: 110 }}>
              <pre style={{ margin: 0 }}>
                {JSON.stringify(v2Def?.sample_payload || { target: { id: 123 } }, null, 2)}
              </pre>
            </div>

            <span style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
              OpenAPI JSON Schema
            </span>
            <div className="json-box" style={{ maxHeight: 180 }}>
              <pre style={{ margin: 0 }}>
                {JSON.stringify(v2Def?.json_schema || {}, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      ) : activeTab === 'active_schema' ? (
        /* Active Schema Full Inspector */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                {schemaInfo?.schema_name} ({schemaInfo?.active_version})
              </span>
              <p style={{ fontSize: '0.775rem', color: 'var(--text-muted)' }}>
                {schemaInfo?.description}
              </p>
            </div>
            <div className="badge badge-info">Authoritative State</div>
          </div>

          <span style={{ fontSize: '0.725rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
            Complete JSON Schema
          </span>
          <div className="json-box" style={{ maxHeight: 320 }}>
            <pre style={{ margin: 0 }}>
              {JSON.stringify(schemaInfo?.json_schema || {}, null, 2)}
            </pre>
          </div>
        </div>
      ) : (
        /* Tool Registry Tab */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                Registered Tool: {studentTool?.tool_name || 'student_service'}
              </span>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Endpoint: <code>{studentTool?.method} {studentTool?.endpoint}</code> | Version in Registry: <strong>{studentTool?.active_version || 'v1'}</strong>
              </p>
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              Last Updated: {studentTool?.last_updated ? new Date(studentTool.last_updated).toLocaleTimeString() : 'N/A'}
            </span>
          </div>

          <span style={{ fontSize: '0.725rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
            Contract Version History
          </span>
          <div className="json-box" style={{ maxHeight: 220 }}>
            <pre style={{ margin: 0 }}>
              {JSON.stringify(studentTool?.version_history || [], null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};
