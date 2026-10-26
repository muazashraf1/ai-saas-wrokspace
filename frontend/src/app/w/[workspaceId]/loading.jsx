export default function WorkspaceLoading() {
  return (
    <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header Skeleton */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ width: '220px', height: '28px', background: 'var(--surface-border)', borderRadius: 'var(--radius-sm)', opacity: 0.6 }} className="animate-pulse" />
          <div style={{ width: '340px', height: '16px', background: 'var(--surface-border)', borderRadius: 'var(--radius-sm)', opacity: 0.4 }} className="animate-pulse" />
        </div>
        <div style={{ width: '120px', height: '36px', background: 'var(--surface-border)', borderRadius: 'var(--radius-md)', opacity: 0.5 }} className="animate-pulse" />
      </div>

      {/* Content Skeleton Card */}
      <div className="card" style={{ padding: '2.5rem', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '320px', gap: '1rem' }}>
        <div style={{ width: '48px', height: '48px', borderRadius: '50%', border: '3px solid var(--surface-border)', borderTopColor: 'var(--primary)', animation: 'spin 0.8s linear infinite' }} />
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Loading workspace data...</p>
      </div>
    </div>
  );
}
