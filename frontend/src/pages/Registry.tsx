import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { registryApi } from '../api/client'

export default function RegistryPage() {
    const [query, setQuery] = useState('')
    const [searching, setSearching] = useState(false)
    const [result, setResult] = useState<any>(null)
    const [searchError, setSearchError] = useState('')

    const { data: blacklist, isLoading } = useQuery({ queryKey: ['blacklist'], queryFn: () => registryApi.blacklist().then(r => r.data) })

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault(); if (!query) return
        setSearching(true); setResult(null); setSearchError('')
        try { setResult((await registryApi.search(query)).data) }
        catch (e: any) { setSearchError(e.response?.data?.detail || 'Registry search failed') }
        finally { setSearching(false) }
    }

    const riskColor = (s: number) => s >= 75 ? '#E53935' : s >= 50 ? '#F57C00' : s >= 25 ? '#F9A825' : '#2E7D32'

    return (
        <div>
            <div className="page-header">
                <div>
                    <div className="page-title">Hash Registry &amp; Blacklist</div>
                    <div className="page-subtitle">Immutable cross-ledger record lookup · Flagged profile registry</div>
                </div>
            </div>

            {/* Search */}
            <div className="card" style={{ marginBottom: 20 }}>
                <div className="card-title">UNIVERSAL HASH LOOKUP</div>
                <form onSubmit={handleSearch} style={{ display: 'flex', gap: 10 }}>
                    <div style={{ flex: 1, position: 'relative' }}>
                        <svg style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--gray-dark)' }} width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg>
                        <input
                            id="hash-search-input"
                            value={query}
                            onChange={e => setQuery(e.target.value)}
                            placeholder="Enter SHA-256 hash, profile hash, or evidence hash…"
                            style={{ width: '100%', paddingLeft: 36, background: '#F7F8FC', border: '1.5px solid var(--gray)', borderRadius: 'var(--radius-sm)', padding: '10px 14px 10px 36px', fontSize: 13, fontFamily: 'Courier New, monospace', color: 'var(--text-navy)' }}
                        />
                    </div>
                    <button id="search-btn" type="submit" className="btn btn-primary" style={{ flexShrink: 0 }} disabled={searching}>
                        {searching ? <div className="spinner spinner-navy" style={{ width: 15, height: 15 }} /> : 'Search Ledger'}
                    </button>
                </form>
                {searchError && <div className="alert alert-error" style={{ marginTop: 12 }}>{searchError}</div>}

                {result && (
                    <div style={{ marginTop: 16, padding: 16, background: result.found ? 'rgba(46,125,50,.05)' : '#F7F8FC', borderRadius: 10, border: `1px solid ${result.found ? 'rgba(46,125,50,.2)' : 'var(--gray)'}` }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                            {result.found
                                ? <><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#2E7D32" strokeWidth="2"><polyline points="20 6 9 17 4 12" /></svg><span style={{ fontWeight: 700, color: '#2E7D32', fontSize: 13 }}>Record found on immutable ledger</span></>
                                : <><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#F57C00" strokeWidth="2"><circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></svg><span style={{ fontWeight: 700, color: '#F57C00', fontSize: 13 }}>Hash not found in registry</span></>
                            }
                        </div>
                        {result.found && <pre style={{ fontSize: 11, fontFamily: 'Courier New,monospace', color: 'var(--text-muted)', whiteSpace: 'pre-wrap', wordBreak: 'break-all', maxHeight: 180, overflow: 'auto' }}>{JSON.stringify(result, null, 2)}</pre>}
                    </div>
                )}
            </div>

            {/* Blacklist */}
            <div className="card">
                <div className="card-title">FLAGGED PROFILE BLACKLIST <span style={{ fontWeight: 500, color: 'var(--text-muted)', fontSize: 11, letterSpacing: 0, textTransform: 'none' }}>— {(blacklist || []).length} profiles</span></div>
                {isLoading ? <div className="loading-center"><div className="spinner" />Loading blacklist…</div> : (
                    <div className="table-wrap">
                        <table>
                            <thead><tr><th>Profile Hash</th><th>Platform</th><th>Risk Score</th><th>Risk Level</th><th>Status</th><th>Case</th><th>Flagged</th></tr></thead>
                            <tbody>
                                {(blacklist || []).map((p: any) => (
                                    <tr key={p.id || p.profile_hash}>
                                        <td><span className="hash-mono">{(p.profile_hash || '').slice(0, 18)}…</span></td>
                                        <td style={{ textTransform: 'capitalize', color: 'var(--text-body)' }}>{p.platform}</td>
                                        <td>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                                <div style={{ width: 70 }}><div className="risk-bar-wrap"><div className="risk-bar" style={{ width: `${p.risk_score}%`, background: riskColor(p.risk_score) }} /></div></div>
                                                <span style={{ fontSize: 12, fontWeight: 700, color: riskColor(p.risk_score) }}>{p.risk_score?.toFixed(0)}</span>
                                            </div>
                                        </td>
                                        <td><span className={`badge badge-${p.risk_score >= 75 ? 'critical' : p.risk_score >= 50 ? 'high' : 'medium'}`}>{p.risk_score >= 75 ? 'CRITICAL' : p.risk_score >= 50 ? 'HIGH' : 'MEDIUM'}</span></td>
                                        <td><span className="badge badge-flagged">FLAGGED</span></td>
                                        <td><span className="hash-mono">{(p.case_id || '').slice(0, 8)}…</span></td>
                                        <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>{p.created_at ? new Date(p.created_at).toLocaleDateString('en-IN') : '—'}</td>
                                    </tr>
                                ))}
                                {(!blacklist || blacklist.length === 0) && <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 40 }}>No flagged profiles in the registry</td></tr>}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    )
}
