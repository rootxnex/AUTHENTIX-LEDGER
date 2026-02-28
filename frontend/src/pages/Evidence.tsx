import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { evidenceApi, casesApi } from '../api/client'
import { useParams } from 'react-router-dom'
import { formatDistanceToNow } from 'date-fns'
import type { EvidenceRecord, Case } from '../types'

export default function EvidencePage() {
    const { caseId: paramCaseId } = useParams()
    const [selectedCase, setSelectedCase] = useState(paramCaseId || '')
    const [evidenceType, setEvidenceType] = useState('SCREENSHOT')
    const [uploading, setUploading] = useState(false)
    const [uploadMsg, setUploadMsg] = useState('')
    const [uploadError, setUploadError] = useState('')
    const [showModal, setShowModal] = useState(false)
    const fileRef = useRef<HTMLInputElement>(null)
    const qc = useQueryClient()

    const { data: casesData } = useQuery({ queryKey: ['cases'], queryFn: () => casesApi.list().then(r => r.data) })
    const cases: Case[] = casesData?.items || []

    const { data: evidenceList, isLoading } = useQuery({
        queryKey: ['evidence', selectedCase],
        queryFn: () => selectedCase ? evidenceApi.listByCase(selectedCase).then(r => r.data) : Promise.resolve([]),
        enabled: !!selectedCase,
    })

    const handleUpload = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!fileRef.current?.files?.[0] || !selectedCase) return
        setUploading(true); setUploadMsg(''); setUploadError('')
        const form = new FormData()
        form.append('file', fileRef.current.files[0])
        form.append('case_id', selectedCase)
        form.append('evidence_type', evidenceType)
        try {
            await evidenceApi.upload(form)
            qc.invalidateQueries({ queryKey: ['evidence', selectedCase] })
            setUploadMsg('Evidence encrypted, hashed, and anchored on blockchain.')
            setShowModal(false)
            if (fileRef.current) fileRef.current.value = ''
        } catch (e: any) { setUploadError(e.response?.data?.detail || 'Upload failed') }
        finally { setUploading(false) }
    }

    const evidence: EvidenceRecord[] = evidenceList || []

    return (
        <div>
            <div className="page-header">
                <div>
                    <div className="page-title">Evidence Registry</div>
                    <div className="page-subtitle">AES-256-GCM encrypted · SHA-256 blockchain-anchored · Section 65B compliant</div>
                </div>
                <button className="btn btn-primary" onClick={() => setShowModal(true)}>
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>
                    Upload Evidence
                </button>
            </div>

            {uploadMsg && <div className="alert alert-success" style={{ marginBottom: 20 }}><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12" /></svg>{uploadMsg}</div>}

            {/* Case selector + security info */}
            <div className="grid-2" style={{ marginBottom: 20, alignItems: 'start' }}>
                <div className="card">
                    <div className="card-title">FILTER BY CASE</div>
                    <select className="form-select" value={selectedCase} onChange={e => setSelectedCase(e.target.value)}>
                        <option value="">— All Cases —</option>
                        {cases.map(c => <option key={c.id} value={c.id}>{c.title}</option>)}
                    </select>
                    {selectedCase && <div style={{ marginTop: 10, fontSize: 12, color: 'var(--text-muted)' }}>{evidence.length} evidence item{evidence.length !== 1 ? 's' : ''} in this case</div>}
                </div>
                <div className="card" style={{ background: '#F7FAFF', border: '1px solid var(--teal-border)' }}>
                    <div className="card-title"><span style={{ color: 'var(--teal)' }}>SECURITY PROTOCOL</span></div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                        {['AES-256-GCM Encryption', 'SHA-256 Hash Anchoring', 'MinIO Off-Chain Storage', 'Section 65B Certificate', 'Immutable Audit Trail', 'RBAC Access Control'].map(t => (
                            <div key={t} style={{ display: 'flex', gap: 6, alignItems: 'center', fontSize: 11, color: 'var(--text-body)' }}>
                                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#2E7D32" strokeWidth="2.5"><polyline points="20 6 9 17 4 12" /></svg>
                                {t}
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Table */}
            <div className="card">
                <div className="card-title">EVIDENCE RECORDS <span style={{ color: 'var(--text-muted)', fontWeight: 400, fontSize: 11, textTransform: 'none', letterSpacing: 0 }}>— Click row to verify integrity</span></div>
                {!selectedCase ? (
                    <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 40 }}>Select a case above to view its evidence records</div>
                ) : isLoading ? <div className="loading-center"><div className="spinner" />Loading evidence…</div> : (
                    <div className="table-wrap">
                        <table>
                            <thead><tr><th>Filename</th><th>Type</th><th>SHA-256 Hash</th><th>Size</th><th>Uploaded</th><th>Blockchain</th><th>Action</th></tr></thead>
                            <tbody>
                                {evidence.map(e => (
                                    <tr key={e.id}>
                                        <td style={{ fontWeight: 600, color: 'var(--navy)' }}>{e.original_filename}</td>
                                        <td><span className="badge badge-teal">{e.evidence_type}</span></td>
                                        <td><span className="hash-mono">{e.evidence_hash.slice(0, 20)}…</span></td>
                                        <td style={{ color: 'var(--text-muted)' }}>{e.file_size_bytes ? (e.file_size_bytes / 1024).toFixed(1) + ' KB' : '—'}</td>
                                        <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>{formatDistanceToNow(new Date(e.created_at), { addSuffix: true })}</td>
                                        <td>
                                            {e.blockchain_tx_id
                                                ? <span style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12, fontWeight: 600, color: 'var(--success)' }}><div className="status-dot dot-green" />Anchored</span>
                                                : <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>Pending</span>}
                                        </td>
                                        <td><button className="btn btn-outline btn-xs" onClick={() => evidenceApi.verify(e.id)}>Verify</button></td>
                                    </tr>
                                ))}
                                {evidence.length === 0 && <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 40 }}>No evidence uploaded for this case yet</td></tr>}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Upload Modal */}
            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <div className="modal-title">Upload Evidence</div>
                            <button className="modal-close" onClick={() => setShowModal(false)}><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg></button>
                        </div>

                        {/* Steps */}
                        <div className="steps" style={{ marginBottom: 22 }}>
                            {['Select File', 'Encrypt', 'Hash & Anchor'].map((s, i) => (
                                <div key={s} style={{ display: 'contents' }}>
                                    <div className="step active"><div className="step-num">{i + 1}</div><span style={{ color: 'var(--teal)', fontSize: 11 }}>{s}</span></div>
                                    {i < 2 && <div className="step-line" />}
                                </div>
                            ))}
                        </div>

                        {uploadError && <div className="alert alert-error">{uploadError}</div>}
                        <form onSubmit={handleUpload}>
                            <div className="form-group">
                                <label className="form-label">Case *</label>
                                <select className="form-select" value={selectedCase} onChange={e => setSelectedCase(e.target.value)} required>
                                    <option value="">— Select Case —</option>
                                    {cases.map(c => <option key={c.id} value={c.id}>{c.title}</option>)}
                                </select>
                            </div>
                            <div className="form-group">
                                <label className="form-label">Evidence Type</label>
                                <select className="form-select" value={evidenceType} onChange={e => setEvidenceType(e.target.value)}>
                                    {['SCREENSHOT', 'JSON_EXPORT', 'REPORT', 'OTHER'].map(t => <option key={t} value={t}>{t.replace('_', ' ')}</option>)}
                                </select>
                            </div>
                            <div className="form-group">
                                <label className="form-label">File *</label>
                                <label className="upload-zone" htmlFor="evidence-file">
                                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--gray-dark)" strokeWidth="1.5" style={{ margin: '0 auto 8px', display: 'block' }}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" /></svg>
                                    <div style={{ color: 'var(--navy)', fontWeight: 600, fontSize: 13 }}>Click to select or drag &amp; drop</div>
                                    <div style={{ color: 'var(--text-muted)', fontSize: 11, marginTop: 4 }}>Screenshots, PDFs, JSON exports — max 50MB</div>
                                </label>
                                <input type="file" id="evidence-file" ref={fileRef} style={{ display: 'none' }} required />
                            </div>
                            <div className="alert alert-info" style={{ marginBottom: 16 }}>
                                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><line x1="12" y1="16" x2="12" y2="12" /><line x1="12" y1="8" x2="12.01" y2="8" /></svg>
                                File will be AES-256-GCM encrypted before storage. Only the SHA-256 hash is anchored on the blockchain.
                            </div>
                            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
                                <button type="button" className="btn btn-ghost" onClick={() => setShowModal(false)}>Cancel</button>
                                <button id="upload-evidence-btn" type="submit" className="btn btn-primary" disabled={uploading}>
                                    {uploading ? <><div className="spinner spinner-navy" style={{ width: 14, height: 14 }} />Encrypting & Anchoring…</> : 'Upload & Anchor'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    )
}
