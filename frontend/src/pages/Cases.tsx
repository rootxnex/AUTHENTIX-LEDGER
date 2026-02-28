import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { casesApi } from '../api/client'
import { formatDistanceToNow } from 'date-fns'
import { useNavigate } from 'react-router-dom'
import type { Case } from '../types'

export default function CasesPage() {
    const qc = useQueryClient()
    const navigate = useNavigate()
    const [showModal, setShowModal] = useState(false)
    const [tab, setTab] = useState<'all' | 'open' | 'closed'>('all')
    const [form, setForm] = useState({ title: '', description: '', fir_number: '', owner_unit: '' })
    const [error, setError] = useState('')

    const { data, isLoading } = useQuery({ queryKey: ['cases'], queryFn: () => casesApi.list().then(r => r.data) })
    const cases: Case[] = data?.items || []
    const filtered = tab === 'all' ? cases : cases.filter(c => c.status.toLowerCase() === tab)

    const createMutation = useMutation({
        mutationFn: (d: object) => casesApi.create(d),
        onSuccess: () => { qc.invalidateQueries({ queryKey: ['cases'] }); setShowModal(false); setForm({ title: '', description: '', fir_number: '', owner_unit: '' }); setError('') },
        onError: (e: any) => setError(e.response?.data?.detail || 'Failed to create case'),
    })

    return (
        <div>
            <div className="page-header">
                <div>
                    <div className="page-title">Investigations</div>
                    <div className="page-subtitle">{cases.length} total · {cases.filter(c => c.status === 'OPEN').length} active</div>
                </div>
                <button className="btn btn-primary" id="new-case-btn" onClick={() => setShowModal(true)}>
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>
                    New Case
                </button>
            </div>

            {/* Summary pills */}
            <div className="grid-3" style={{ gap: 14, marginBottom: 22 }}>
                {[{ label: 'Total Cases', v: cases.length, c: 'var(--navy)' }, { label: 'Open', v: cases.filter(c => c.status === 'OPEN').length, c: '#00B8D9' }, { label: 'Closed', v: cases.filter(c => c.status === 'CLOSED').length, c: 'var(--text-muted)' }].map(s => (
                    <div key={s.label} style={{ background: 'var(--white)', borderRadius: 12, padding: '14px 18px', boxShadow: 'var(--shadow-card)', border: '1px solid rgba(10,31,68,.06)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '.06em' }}>{s.label}</span>
                        <span style={{ fontSize: 24, fontWeight: 800, color: s.c }}>{s.v}</span>
                    </div>
                ))}
            </div>

            {/* Tabs */}
            <div className="card">
                <div className="tabs">
                    {(['all', 'open', 'closed'] as const).map(t => (
                        <div key={t} className={`tab${tab === t ? ' active' : ''}`} onClick={() => setTab(t)}>
                            {t.charAt(0).toUpperCase() + t.slice(1)}&nbsp;
                            <span style={{ fontSize: 11, color: tab === t ? 'var(--teal)' : 'var(--text-muted)' }}>{t === 'all' ? cases.length : cases.filter(c => c.status.toLowerCase() === t).length}</span>
                        </div>
                    ))}
                </div>

                {isLoading ? <div className="loading-center"><div className="spinner" /><span>Loading cases…</span></div> : (
                    <div className="table-wrap">
                        <table>
                            <thead><tr><th>Case Title</th><th>FIR Number</th><th>Unit</th><th>Profiles</th><th>Evidence</th><th>Status</th><th>Created</th><th></th></tr></thead>
                            <tbody>
                                {filtered.map(c => (
                                    <tr key={c.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/evidence/${c.id}`)}>
                                        <td><div style={{ fontWeight: 600, color: 'var(--navy)' }}>{c.title}</div>{c.fir_number && <div className="hash-mono" style={{ marginTop: 3 }}>{c.fir_number}</div>}</td>
                                        <td><span className="hash-mono">{c.fir_number || '—'}</span></td>
                                        <td style={{ color: 'var(--text-muted)' }}>{c.owner_unit || '—'}</td>
                                        <td style={{ fontWeight: 600, color: 'var(--navy)' }}>{c.profile_count}</td>
                                        <td style={{ fontWeight: 600, color: 'var(--navy)' }}>{c.evidence_count}</td>
                                        <td><span className={`badge badge-${c.status.toLowerCase()}`}>{c.status}</span></td>
                                        <td style={{ color: 'var(--text-muted)', fontSize: 12, whiteSpace: 'nowrap' }}>{formatDistanceToNow(new Date(c.created_at), { addSuffix: true })}</td>
                                        <td><button className="btn btn-outline btn-xs" onClick={e => { e.stopPropagation(); navigate(`/evidence/${c.id}`) }}>View →</button></td>
                                    </tr>
                                ))}
                                {filtered.length === 0 && <tr><td colSpan={8} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 40 }}>No cases in this view. Create a new investigation to begin.</td></tr>}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Modal */}
            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <div className="modal-title">Open New Investigation Case</div>
                            <button className="modal-close" onClick={() => setShowModal(false)}>
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
                            </button>
                        </div>
                        {error && <div className="alert alert-error">{error}</div>}
                        <form onSubmit={e => { e.preventDefault(); createMutation.mutate(form) }}>
                            <div className="form-group">
                                <label className="form-label">Case Title *</label>
                                <input className="form-input" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} placeholder="e.g. Operation Kali – Social Media Fraud Network" required />
                            </div>
                            <div className="grid-2">
                                <div className="form-group">
                                    <label className="form-label">FIR Number</label>
                                    <input className="form-input" value={form.fir_number} onChange={e => setForm({ ...form, fir_number: e.target.value })} placeholder="FIR/2024/MH/001234" />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Investigating Unit</label>
                                    <input className="form-input" value={form.owner_unit} onChange={e => setForm({ ...form, owner_unit: e.target.value })} placeholder="Maharashtra CID – Cybercrime" />
                                </div>
                            </div>
                            <div className="form-group">
                                <label className="form-label">Case Description</label>
                                <textarea className="form-textarea" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} placeholder="Describe the scope, suspected offences, and intelligence summary…" />
                            </div>
                            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
                                <button type="button" className="btn btn-ghost" onClick={() => setShowModal(false)}>Cancel</button>
                                <button type="submit" className="btn btn-primary" disabled={createMutation.isPending}>
                                    {createMutation.isPending ? <><div className="spinner spinner-navy" style={{ width: 14, height: 14 }} />Creating…</> : 'Create Case'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    )
}
