'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { useWorkspace } from '@/context/WorkspaceContext';
import {
  getDocuments,
  uploadDocument,
  retryDocument,
  deleteDocument,
} from '@/lib/api';
import { formatDate, formatBytes } from '@/lib/utils';
import {
  UploadCloud,
  FileText,
  RefreshCw,
  Trash2,
  AlertCircle,
  CheckCircle2,
  Clock,
  XCircle,
  FileCheck,
  ShieldAlert,
} from 'lucide-react';

function DocumentsContent() {
  const params = useParams();
  const workspaceId = params?.workspaceId;
  const { role, usage } = useWorkspace();

  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [actionLoadingId, setActionLoadingId] = useState(null);

  const fileInputRef = useRef(null);
  const pollIntervalRef = useRef(null);

  const fetchDocs = useCallback(async () => {
    const res = await getDocuments(workspaceId);
    if (res.data) {
      setDocuments(res.data);
    } else {
      setError(res.error || 'Failed to load documents.');
    }
    setLoading(false);
  }, [workspaceId]);

  useEffect(() => {
    const timer = setTimeout(fetchDocs, 0);
    return () => {
      clearTimeout(timer);
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [fetchDocs]);

  useEffect(() => {
    const hasPending = documents.some(
      (doc) => doc.status === 'processing' || doc.status === 'uploaded'
    );
    if (hasPending && !pollIntervalRef.current) {
      pollIntervalRef.current = setInterval(fetchDocs, 3000);
    } else if (!hasPending && pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, [documents, fetchDocs]);

  const handleFileUpload = async (file) => {
    if (!file) return;

    setError('');
    setSuccessMsg('');

    // Client-side validation: Max 10MB
    const maxFileMb = usage?.max_file_mb_limit ?? 10;
    const MAX_SIZE_BYTES = maxFileMb * 1024 * 1024;
    if (file.size > MAX_SIZE_BYTES) {
      setError(`File size (${formatBytes(file.size)}) exceeds maximum limit of ${maxFileMb} MB.`);
      return;
    }

    // Client-side validation: Allowed extensions
    const ext = file.name.split('.').pop().toLowerCase();
    if (ext !== 'pdf' && ext !== 'txt') {
      setError('Unsupported file type. Only .pdf and .txt documents are permitted.');
      return;
    }

    setUploading(true);

    const res = await uploadDocument(workspaceId, file);
    setUploading(false);

    if (res.error) {
      if (res.status === 409) {
        setError(
          'Duplicate upload detected: This file has already been uploaded to this workspace (SHA-256 match).'
        );
      } else {
        setError(res.error);
      }
    } else {
      setSuccessMsg(`"${file.name}" uploaded successfully. Ingestion in progress...`);
      fetchDocs();
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleRetry = async (docId) => {
    setActionLoadingId(docId);
    setError('');
    const res = await retryDocument(workspaceId, docId);
    setActionLoadingId(null);
    if (res.error) {
      setError(res.error);
    } else {
      setSuccessMsg('Ingestion restarted for document.');
      fetchDocs();
    }
  };

  const handleDelete = async (docId, name) => {
    if (!confirm(`Are you sure you want to delete "${name}"? This will delete all its text chunks and vector embeddings.`)) {
      return;
    }

    setActionLoadingId(docId);
    setError('');
    const res = await deleteDocument(workspaceId, docId);
    setActionLoadingId(null);
    if (res.error) {
      setError(res.error);
    } else {
      setSuccessMsg(`Document "${name}" deleted.`);
      fetchDocs();
    }
  };

  return (
    <div style={{ maxWidth: '1080px', margin: '0 auto' }}>
      {/* Page Header */}
      <div style={{ marginBottom: '1.75rem' }}>
        <h1 style={{ fontSize: '1.6rem', fontWeight: 700, letterSpacing: '-0.02em', marginBottom: '0.35rem' }}>
          Document Ingestion
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          Upload PDF or TXT files. Chunks and pgvector embeddings are isolated strictly to this workspace.
        </p>
      </div>

      {/* Notifications */}
      {error && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.85rem 1rem',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--status-failed-bg)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: '#fca5a5',
            fontSize: '0.85rem',
            marginBottom: '1.25rem',
          }}
        >
          <AlertCircle size={16} style={{ flexShrink: 0 }} />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.85rem 1rem',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--status-ready-bg)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            color: '#6ee7b7',
            fontSize: '0.85rem',
            marginBottom: '1.25rem',
          }}
        >
          <CheckCircle2 size={16} style={{ flexShrink: 0 }} />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Upload Dropzone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className="card"
        style={{
          border: `2px dashed ${dragActive ? 'var(--primary)' : 'rgba(255, 255, 255, 0.15)'}`,
          background: dragActive ? 'rgba(59, 130, 246, 0.05)' : 'var(--bg-card)',
          padding: '2.5rem 1.5rem',
          textAlign: 'center',
          cursor: uploading ? 'wait' : 'pointer',
          marginBottom: '2rem',
          transition: 'var(--transition)',
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt"
          onChange={(e) => handleFileUpload(e.target.files?.[0])}
          style={{ display: 'none' }}
        />

        <div
          style={{
            width: 48,
            height: 48,
            borderRadius: '50%',
            background: 'rgba(59, 130, 246, 0.1)',
            color: 'var(--primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1rem auto',
          }}
        >
          <UploadCloud size={24} />
        </div>

        <div style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.35rem' }}>
          {uploading ? 'Uploading and queueing document...' : 'Click or drag files here to upload'}
        </div>
        <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
          Supported formats: PDF, TXT • Maximum file size: 10 MB per document
        </div>
      </div>

      {/* Documents List */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 600 }}>
            Workspace Documents ({documents.length})
          </h2>
          <button onClick={fetchDocs} className="btn btn-ghost" style={{ padding: '0.4rem 0.65rem', fontSize: '0.8rem' }}>
            <RefreshCw size={14} />
            <span>Refresh</span>
          </button>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
            Loading documents...
          </div>
        ) : documents.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '3rem 1.5rem', color: 'var(--text-secondary)' }}>
            <FileText size={36} color="var(--text-muted)" style={{ margin: '0 auto 0.75rem auto' }} />
            <div style={{ fontWeight: 500, marginBottom: '0.25rem' }}>No documents uploaded yet</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Upload your company policies, manuals, or reports to start answering questions with verified citations.
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {documents.map((doc) => {
              const isReady = doc.status === 'ready';
              const isProcessing = doc.status === 'processing' || doc.status === 'uploaded';
              const isFailed = doc.status === 'failed';

              return (
                <div
                  key={doc.id}
                  className="card"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '1rem 1.25rem',
                  }}
                >
                  {/* Left: Icon & Name */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem', minWidth: 0 }}>
                    <div
                      style={{
                        width: 38,
                        height: 38,
                        borderRadius: 'var(--radius-sm)',
                        background: 'rgba(255, 255, 255, 0.04)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'var(--text-secondary)',
                        flexShrink: 0,
                      }}
                    >
                      <FileText size={20} />
                    </div>

                    <div style={{ minWidth: 0 }}>
                      <div
                        style={{
                          fontWeight: 600,
                          fontSize: '0.9rem',
                          color: 'var(--text-primary)',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                        }}
                      >
                        {doc.original_name}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', gap: '0.5rem', marginTop: '0.15rem' }}>
                        <span>{formatBytes(doc.size_bytes)}</span>
                        <span>•</span>
                        <span>{doc.page_count ? `${doc.page_count} pages` : 'Text format'}</span>
                        <span>•</span>
                        <span>{formatDate(doc.created_at)}</span>
                      </div>
                      {doc.failure_reason && (
                        <div style={{ color: 'var(--status-failed)', fontSize: '0.75rem', marginTop: '0.25rem' }}>
                          Reason: {doc.failure_reason}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Right: Status Badge & Actions */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexShrink: 0 }}>
                    {/* Status Badge */}
                    {isReady && (
                      <span className="badge badge-ready">
                        <CheckCircle2 size={12} />
                        <span>Ready ({doc.chunk_count || 'Chunks'} Active)</span>
                      </span>
                    )}

                    {isProcessing && (
                      <span className="badge badge-processing">
                        <span className="animate-pulse-dot" style={{ width: 6, height: 6, borderRadius: '50%', background: '#fbbf24' }}></span>
                        <span>Processing Chunks...</span>
                      </span>
                    )}

                    {isFailed && (
                      <span className="badge badge-failed">
                        <XCircle size={12} />
                        <span>Failed</span>
                      </span>
                    )}

                    {/* Actions */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                      {isFailed && (
                        <button
                          onClick={() => handleRetry(doc.id)}
                          disabled={actionLoadingId === doc.id}
                          className="btn btn-secondary"
                          style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem' }}
                          title="Retry Ingestion"
                        >
                          <RefreshCw size={13} className={actionLoadingId === doc.id ? 'animate-spin' : ''} />
                          <span>Retry</span>
                        </button>
                      )}

                      <button
                        onClick={() => handleDelete(doc.id, doc.original_name)}
                        disabled={actionLoadingId === doc.id}
                        className="btn btn-danger"
                        style={{ padding: '0.35rem 0.55rem' }}
                        title="Delete Document"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default function DocumentsPage() {
  return (
    <React.Suspense fallback={<div style={{ padding: '2rem', color: 'var(--text-secondary)' }}>Loading documents...</div>}>
      <DocumentsContent />
    </React.Suspense>
  );
}
