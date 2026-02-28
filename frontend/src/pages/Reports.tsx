import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { reportsApi, casesApi } from '../api/client'
import { useParams } from 'react-router-dom'
import type { Case } from '../types'

export default function ReportsPage() {
    const { caseId: paramCaseId } = useParams()
    const [selectedCase, setSelectedCase] = useState(paramCaseId || '')
    const [notes, setNotes] = useState('')
    const [generated, setGenerated] = useState<any>(null)
    const [error, setError] = useState('')

    const { data: casesData } = useQuery({ queryKey: ['cases'], queryFn: () => casesApi.list().then(r => r.data) })
    const cases: Case[] = casesData?.items || []

    const genMutation = useMutation({
        mutationFn: () => reportsApi.generate(selectedCase, notes),
        onSuccess: r => { setGenerated(r.data); setError('') },
        onError: (e: any) => setError(e.response?.data?.detail || 'Report generation failed'),
    })

    return (
        <div>
            <div className="page-header">
                <div>
                    <div className="page-title">Court Reports</div>
                    <div className="page-subtitle">Section 65B compliant PDF · Blockchain-verified hash proof · Investigator signature block</div>
                </div>
            </div>

            <div className="grid-2" style={{ alignItems: 'start' }}>
                {/* ── Generator ──────────────────────────────────── */}
                <div className="card">
                    <div className="card-title">GENERATE REPORT</div>
                    {error && <div className="alert alert-error">{error}</div>}

                    <div className="form-group">
                        <label className="form-label">Select Case *</label>
                        <select className="form-select" value={selectedCase} onChange={e => setSelectedCase(e.target.value)}>
                            <option value="">— Select Investigation Case —</option>
                            {cases.map(c => <option key={c.id} value={c.id}>{c.title}</option>)}
                        </select>
                    </div>
                    <div className="form-group">
                        <label className="form-label">Investigator Notes</label>
                        <textarea className="form-textarea" value={notes} onChange={e => setNotes(e.target.value)} rows={5} placeholder="Insert additional observations, summary of findings, legal references, or court directions…" />
                    </div>

                    <button
                        id="generate-report-btn"
                        className="btn btn-primary"
                        style={{ width: '100%', justifyContent: 'center', padding: 11 }}
                        onClick={() => genMutation.mutate()}
                        disabled={!selectedCase || genMutation.isPending}
                    >
                        {genMutation.isPending ? <><div className="spinner spinner-navy" style={{ width: 15, height: 15 }} />Generating PDF…</> : 'Generate Court Report'}
                    </button>

                    <div className="divider" />
                    <div className="section-title">REPORT CONTENTS</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
                        {[
                            'Case summary, FIR details, investigating officer',
                            'All analyzed profiles with AI risk scores',
                            'SHAP explainability factors per profile',
                            'Evidence SHA-256 hashes & blockchain TX IDs',
                            'Section 65B certificate (IT Act compliance)',
                            'Investigator signature block',
                        ].map((t, i) => (
                            <div key={i} style={{ display: 'flex', gap: 8, fontSize: 12, alignItems: 'flex-start' }}>
                                <span style={{ color: 'var(--teal)', fontWeight: 700, flexShrink: 0 }}>{i + 1}.</span>
                                <span style={{ color: 'var(--text-muted)' }}>{t}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* ── Report Result ───────────────────────────────── */}
                <div>
                    {generated ? (
                        <div className="card" style={{ border: '1px solid rgba(46,125,50,.25)' }}>
                            {/* Header */}
                            <div style={{ display: 'flex', gap: 14, alignItems: 'flex-start', marginBottom: 20 }}>
                                <div style={{ width: 48, height: 48, borderRadius: 12, background: 'rgba(46,125,50,.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2E7D32" strokeWidth="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /></svg>
                                </div>
                                <div>
                                    <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--navy)' }}>Report Generated</div>
                                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>{generated.generated_at ? new Date(generated.generated_at).toLocaleString('en-IN') : ''}</div>
                                    <span className="badge badge-open" style={{ marginTop: 6, display: 'inline-flex' }}>READY FOR COURT</span>
                                </div>
                            </div>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 20 }}>
                                <div className="data-pill">
                                    <span className="data-pill-label">Report ID</span>
                                    <span className="hash-mono" style={{ fontSize: 12 }}>{generated.report_id}</span>
                                </div>
                                <div className="data-pill">
                                    <span className="data-pill-label">Document Hash (SHA-256)</span>
                                    <span className="hash-mono" style={{ fontSize: 11 }}>{(generated.hash_proof || '').slice(0, 24)}…</span>
                                </div>
                                <div className="data-pill">
                                    <span className="data-pill-label">Compliance</span>
                                    <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--success)' }}>Section 65B | IT Act 2000</span>
                                </div>
                            </div>

                            <a href={generated.download_url} className="btn btn-primary" style={{ display: 'inline-flex', width: '100%', justifyContent: 'center' }} target="_blank" rel="noreferrer">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></svg>
                                Download Court-Ready PDF
                            </a>

                            <div className="alert alert-info" style={{ marginTop: 14 }}>
                                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><line x1="12" y1="16" x2="12" y2="12" /></svg>
                                Verify document integrity by comparing SHA-256 hash above with the hash printed on the PDF cover page.
                            </div>
                        </div>
                    ) : (
                        <div className="card" style={{ textAlign: 'center', padding: '56px 24px', border: '2px dashed var(--gray)' }}>
                            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--gray-mid)" strokeWidth="1.5" style={{ margin: '0 auto 14px' }}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /></svg>
                            <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--navy)', marginBottom: 6 }}>No Report Generated</div>
                            <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>Select a case and generate a Section 65B compliant court report</div>
                        </div>
                    )}

                    {/* Legal note */}
                    <div className="card" style={{ marginTop: 16, background: '#FFFBF0', border: '1px solid rgba(245,124,0,.2)' }}>
                        <div className="card-title" style={{ color: '#F57C00' }}>LEGAL NOTICE</div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.7 }}>
                            Reports generated by AUTHENTIX LEDGER are admissible as electronic evidence under Section 65B of the Indian Evidence Act, 1872. The certifying officer must sign the Section 65B certificate before submission to court.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
