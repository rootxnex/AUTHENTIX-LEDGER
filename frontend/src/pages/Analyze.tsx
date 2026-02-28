import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { profilesApi, casesApi } from '../api/client'
import type { ProfileAnalysis, Case } from '../types'

const riskColor = (level: string) => ({ CRITICAL: '#E53935', HIGH: '#F57C00', MEDIUM: '#F9A825', LOW: '#2E7D32' }[level] || 'var(--navy)')
const riskBg = (level: string) => ({ CRITICAL: 'rgba(229,57,53,.08)', HIGH: 'rgba(245,124,0,.08)', MEDIUM: 'rgba(249,168,37,.08)', LOW: 'rgba(46,125,50,.08)' }[level] || 'var(--gray)')

export default function AnalyzePage() {
    const [form, setForm] = useState({ profile_url: '', platform: 'twitter', case_id: '' })
    const [result, setResult] = useState<ProfileAnalysis | null>(null)
    const [error, setError] = useState('')

    const { data: casesData } = useQuery({ queryKey: ['cases'], queryFn: () => casesApi.list().then(r => r.data) })
    const cases: Case[] = casesData?.items || []

    const analyzeMutation = useMutation({
        mutationFn: (d: object) => profilesApi.analyze(d),
        onSuccess: (res) => { setResult(res.data); setError('') },
        onError: (e: any) => setError(e.response?.data?.detail || 'Analysis failed. Check the URL and try again.'),
    })

    return (
        <div>
            <div className="page-header">
                <div>
                    <div className="page-title">Profile Analyzer</div>
                    <div className="page-subtitle">AI-powered fake account &amp; risk scoring engine with blockchain anchoring</div>
                </div>
                <div className="bc-strip" style={{ fontSize: 11 }}>
                    <div className="status-dot dot-green" />
                    AI Engine Online
                </div>
            </div>

            <div className="grid-2" style={{ alignItems: 'start' }}>
                {/* ── Input ─────────────────────────────────────── */}
                <div>
                    <div className="card">
                        <div className="card-title">ANALYSIS REQUEST</div>
                        {error && <div className="alert alert-error">{error}</div>}
                        <form onSubmit={e => { e.preventDefault(); analyzeMutation.mutate(form) }}>
                            <div className="form-group">
                                <label className="form-label">Profile URL *</label>
                                <input id="profile-url-input" className="form-input" value={form.profile_url} onChange={e => setForm({ ...form, profile_url: e.target.value })} placeholder="https://twitter.com/username" required />
                                <span className="form-hint">URL is hashed before processing — no PII stored on ledger</span>
                            </div>
                            <div className="form-group">
                                <label className="form-label">Platform</label>
                                <select className="form-select" value={form.platform} onChange={e => setForm({ ...form, platform: e.target.value })}>
                                    {['twitter', 'instagram', 'facebook', 'telegram', 'linkedin', 'youtube'].map(p => <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>)}
                                </select>
                            </div>
                            <div className="form-group">
                                <label className="form-label">Link to Case *</label>
                                <select className="form-select" value={form.case_id} onChange={e => setForm({ ...form, case_id: e.target.value })} required>
                                    <option value="">— Select Investigation Case —</option>
                                    {cases.map(c => <option key={c.id} value={c.id}>{c.title}</option>)}
                                </select>
                            </div>
                            <button id="analyze-btn" type="submit" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', padding: '11px' }} disabled={analyzeMutation.isPending}>
                                {analyzeMutation.isPending ? <><div className="spinner spinner-navy" style={{ width: 15, height: 15 }} />Running AI Analysis…</> : 'Run AI Analysis'}
                            </button>
                        </form>

                        <div className="divider" />
                        <div className="section-title">SCORING METHODOLOGY</div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
                            {[
                                ['Behavioral Signals', 'Following/follower ratio, posting velocity, account age'],
                                ['Text Analysis', 'Bio spam keywords, post duplication, caption patterns'],
                                ['Graph Features', 'Network centrality, bot cluster proximity, PageRank'],
                                ['Explainability', 'SHAP values — top 5 contributing factors shown'],
                            ].map(([t, d]) => (
                                <div key={t} style={{ display: 'flex', gap: 10, fontSize: 12 }}>
                                    <div style={{ width: 4, borderRadius: 2, background: 'var(--teal)', flexShrink: 0 }} />
                                    <div><span style={{ fontWeight: 600, color: 'var(--navy)' }}>{t}: </span><span style={{ color: 'var(--text-muted)' }}>{d}</span></div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* ── Result ────────────────────────────────────── */}
                <div>
                    {result ? (
                        <div>
                            {/* Score card */}
                            <div className="card" style={{ marginBottom: 16, borderLeft: `4px solid ${riskColor(result.risk_level)}` }}>
                                <div style={{ display: 'flex', gap: 18, alignItems: 'flex-start' }}>
                                    {/* Score ring */}
                                    <div style={{ flexShrink: 0 }}>
                                        <svg width="90" height="90">
                                            <circle cx="45" cy="45" r="38" fill="none" stroke="#E0E0E0" strokeWidth="7" />
                                            <circle cx="45" cy="45" r="38" fill="none" stroke={riskColor(result.risk_level)} strokeWidth="7"
                                                strokeDasharray={`${2 * Math.PI * 38 * result.risk_score / 100} ${2 * Math.PI * 38 * (1 - result.risk_score / 100)}`}
                                                strokeLinecap="round" transform="rotate(-90 45 45)" />
                                            <text x="45" y="44" textAnchor="middle" dominantBaseline="middle" fill={riskColor(result.risk_level)} fontSize="18" fontWeight="800">{result.risk_score}</text>
                                            <text x="45" y="60" textAnchor="middle" fill="#9E9E9E" fontSize="9">/100</text>
                                        </svg>
                                    </div>
                                    <div style={{ flex: 1 }}>
                                        <div style={{ fontSize: 20, fontWeight: 800, color: riskColor(result.risk_level) }}>{result.risk_level} RISK</div>
                                        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 10 }}>{result.platform} · {result.analyzed_at ? new Date(result.analyzed_at).toLocaleString('en-IN') : ''}</div>
                                        <span className={`badge badge-${result.status?.toLowerCase()}`}>{result.status}</span>
                                        {result.blockchain_tx_id && <div style={{ marginTop: 10 }}><div className="section-title" style={{ marginBottom: 4 }}>BLOCKCHAIN TX</div><span className="hash-mono">{result.blockchain_tx_id}</span></div>}
                                    </div>
                                </div>

                                {/* Risk bar */}
                                <div style={{ marginTop: 16 }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-muted)', marginBottom: 5 }}>
                                        <span>Risk Probability</span><span style={{ fontWeight: 700, color: riskColor(result.risk_level) }}>{result.risk_score}%</span>
                                    </div>
                                    <div className="risk-bar-wrap" style={{ height: 8 }}>
                                        <div className={`risk-bar ${result.risk_level.toLowerCase()}`} style={{ width: `${result.risk_score}%` }} />
                                    </div>
                                </div>
                            </div>

                            {/* SHAP factors */}
                            <div className="card">
                                <div className="card-title">AI EXPLAINABILITY — SHAP FACTORS</div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                    {(result.risk_factors || []).map((f, i) => (
                                        <div key={i} style={{ padding: '10px 12px', background: f.direction === 'increases_risk' ? 'rgba(229,57,53,.05)' : 'rgba(46,125,50,.05)', borderRadius: 8, border: `1px solid ${f.direction === 'increases_risk' ? 'rgba(229,57,53,.15)' : 'rgba(46,125,50,.15)'}` }}>
                                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                                                <span style={{ fontWeight: 600, fontSize: 13, color: 'var(--navy)' }}>{f.name.replace(/_/g, ' ')}</span>
                                                <span style={{ fontSize: 12, fontWeight: 700, color: f.direction === 'increases_risk' ? '#E53935' : '#2E7D32' }}>
                                                    {f.direction === 'increases_risk' ? '▲ Increases Risk' : '▼ Reduces Risk'}
                                                </span>
                                            </div>
                                            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{f.description} · SHAP: {f.contribution > 0 ? '+' : ''}{f.contribution.toFixed(4)}</div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="card" style={{ textAlign: 'center', padding: '56px 24px', color: 'var(--text-muted)' }}>
                            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--gray-mid)" strokeWidth="1.5" style={{ margin: '0 auto 14px' }}><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg>
                            <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--navy)', marginBottom: 6 }}>No Analysis Yet</div>
                            <div style={{ fontSize: 13 }}>Enter a profile URL and select a case to run the AI risk scoring engine</div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
