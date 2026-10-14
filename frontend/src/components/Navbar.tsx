import React from 'react';
import { RefreshCw, Server, ShieldCheck, Zap } from 'lucide-react';
import { HealthResponse } from '../types/api';

interface NavbarProps {
  health: HealthResponse | null;
  activeSchemaVersion: string;
  loading: boolean;
  onRefresh: () => void;
  baseUrl: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  health,
  activeSchemaVersion,
  loading,
  onRefresh,
  baseUrl,
}) => {
  const isOnline = health?.status === 'ok';

  return (
    <header
      style={{
        borderBottom: '1px solid var(--border-subtle)',
        background: 'rgba(15, 23, 42, 0.85)',
        backdropFilter: 'blur(8px)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
      }}
    >
      <div
        style={{
          maxWidth: 1440,
          margin: '0 auto',
          padding: '0.875rem 1.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        {/* Brand & Title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            style={{
              width: 34,
              height: 34,
              borderRadius: 6,
              background: 'linear-gradient(135deg, #0284c7, #0ea5e9)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
            }}
          >
            <Zap size={20} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.05rem', fontWeight: 700, letterSpacing: '-0.01em' }}>
              Self-Healing Tool Registry
            </h1>
            <p style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>
              Automatic Runtime API Schema Drift Recovery Dashboard
            </p>
          </div>
        </div>

        {/* Status Indicators & Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          {/* Server Status */}
          <div
            className={`badge ${isOnline ? 'badge-success' : 'badge-danger'}`}
            title={`Backend URL: ${baseUrl}`}
          >
            <Server size={12} />
            <span>{isOnline ? 'API Connected' : 'API Offline'}</span>
          </div>

          {/* Active Schema Version */}
          <div className="badge badge-info" title="Currently expected schema version on /student">
            <ShieldCheck size={12} />
            <span>Active Schema: <strong>{activeSchemaVersion || 'unknown'}</strong></span>
          </div>

          {/* Base URL */}
          <span
            style={{
              fontSize: '0.75rem',
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)',
              background: 'var(--bg-surface)',
              padding: '0.2rem 0.5rem',
              borderRadius: 4,
            }}
          >
            {baseUrl}
          </span>

          {/* Refresh Button */}
          <button
            onClick={onRefresh}
            disabled={loading}
            className="btn btn-secondary"
            title="Refresh all metrics, audit logs, and schemas"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span>{loading ? 'Refreshing...' : 'Refresh'}</span>
          </button>
        </div>
      </div>
    </header>
  );
};
