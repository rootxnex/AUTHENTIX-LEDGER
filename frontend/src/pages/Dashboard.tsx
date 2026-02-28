import { useQuery } from '@tanstack/react-query'
import { casesApi, registryApi } from '../api/client'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import type { Case } from '../types'
import { formatDistanceToNow } from 'date-fns'

const RISK_COLORS = { CRITICAL: '#E53935', HIGH: '#F57C00', MEDIUM: '#F9A825', LOW: '#2E7D32' }

/* ── Circular Gauge SVG ───────────────────────────────────── */
function CircularGauge({ value, max = 100, label }: { value: number; max?: number; label: string }) {
    const r = 52; const circ = 2 * Math.PI * r
    const pct = value / max; const dash = circ * pct; const gap = circ - dash
    const color = value >= 75 ? '#E53935' : value >= 50 ? '#F57C00' : value >= 25 ? '#F9A825' : '#2E7D32'
    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
            <svg width="130" height="130" viewBox="0 0 130 130">
                <circle cx="65" cy="65" r={r} fill="none" stroke="#E0E0E0" strokeWidth="10" />
                <circle cx="65" cy="65" r={r} fill="none" stroke={color} strokeWidth="10"
                    strokeDasharray={`${dash} ${gap}`} strokeLinecap="round"
                    transform="rotate(-90 65 65)" />
                <text x="65" y="60" textAnchor="middle" dominantBaseline="middle" fill={color} fontSize="22" fontWeight="800">{value}</text>
                <text x="65" y="80" textAnchor="middle" fill="#6B7FA3" fontSize="10" fontWeight="600">/100</text>
            </svg>
            <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--navy)' }}>{label}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                    {value >= 75 ? "CRITICAL RISK" : value >= 50 ? "HIGH RISK" : value >= 25 ? "MEDIUM RISK" : "LOW RISK"}
                </div>
            </div>
        </div>
    )
}

/* ── Network Graph Placeholder ─────────────────────────────── */
function NetworkGraph() {
    const nodes = [
        { x: 50, y: 50, flagged: true, r: 12 }, { x: 130, y: 30, flagged: true, r: 9 }, { x: 90, y: 100, flagged: true, r: 10 },
        { x: 200, y: 60, flagged: false, r: 7 }, { x: 270, y: 40, flagged: false, r: 8 }, { x: 310, y: 90, flagged: false, r: 7 },
        { x: 180, y: 130, flagged: false, r: 7 }, { x: 60, y: 150, flagged: true, r: 8 }, { x: 140, y: 170, flagged: false, r: 6 },
        { x: 240, y: 160, flagged: false, r: 7 }, { x: 340, y: 140, flagged: false, r: 6 }, { x: 380, y: 60, flagged: false, r: 8 },
    ]
    const edges = [[0, 1], [0, 2], [1, 2], [0, 7], [3, 4], [4, 5], [3, 6], [6, 8], [8, 9], [9, 10], [10, 11], [5, 11], [3, 9]]
    return (
        <svg width="100%" height="200" style={{ background: '#F7F8FC', borderRadius: 10, border: '1px solid #E0E0E0' }}>
            {/* Grid */}
            {[40, 80, 120, 160].map(y => <line key={y} x1="0" y1={y} x2="100%" y2={y} stroke="#E0E0E0" strokeWidth="0.5" />)}
            {[80, 160, 240, 320, 400].map(x => <line key={x} x1={x} y1="0" x2={x} y2="200" stroke="#E0E0E0" strokeWidth="0.5" />)}
            {/* Edges */}
            {edges.map(([a, b], i) => (
                <line key={i} x1={nodes[a].x} y1={nodes[a].y} x2={nodes[b].x} y2={nodes[b].y}
                    stroke={nodes[a].flagged || nodes[b].flagged ? "rgba(229,57,53,0.3)" : "rgba(0,184,217,0.2)"} strokeWidth="1.5" />
            ))}
            {/* Nodes */}
            {nodes.map((n, i) => (
                <g key={i}>
                    <circle cx={n.x} cy={n.y} r={n.r + 4} fill={n.flagged ? "rgba(229,57,53,0.1)" : "transparent"} />
                    <circle cx={n.x} cy={n.y} r={n.r} fill={n.flagged ? "#E53935" : "#BDBDBD"} opacity="0.9" />
                </g>
            ))}
            {/* Legend */}
            <circle cx="20" cy="185" r="5" fill="#E53935" />
            <text x="30" y="189" fill="#6B7FA3" fontSize="9" fontWeight="600">FLAGGED NODE</text>
            <circle cx="120" cy="185" r="5" fill="#BDBDBD" />
            <text x="130" y="189" fill="#6B7FA3" fontSize="9" fontWeight="600">NEUTRAL NODE</text>
        </svg>
    )
}

export default function DashboardPage() {
    const { data: casesData } = useQuery({ queryKey: ['cases'], queryFn: () => casesApi.list(1, 100).then(r => r.data) })
    const { data: blacklist } = useQuery({ queryKey: ['blacklist'], queryFn: () => registryApi.blacklist().then(r => r.data) })

    const cases: Case[] = casesData?.items || []
    const openCases = cases.filter(c => c.status === 'OPEN').length
    const totalProfiles = cases.reduce((s, c) => s + c.profile_count, 0)
    const totalEvidence = cases.reduce((s, c) => s + c.evidence_count, 0)
    const flagged = (blacklist || []).length

    const riskDist = [
        { level: 'Critical', count: (blacklist || []).filter((p: any) => p.risk_score >= 75).length, color: '#E53935' },
        { level: 'High', count: (blacklist || []).filter((p: any) => p.risk_score >= 50 && p.risk_score < 75).length, color: '#F57C00' },
        { level: 'Medium', count: (blacklist || []).filter((p: any) => p.risk_score >= 25 && p.risk_score < 50).length, color: '#F9A825' },
        { level: 'Low', count: (blacklist || []).filter((p: any) => p.risk_score < 25).length, color: '#2E7D32' },
    ]

    const CustomTooltip = ({ active, payload }: any) => {
        if (!active || !payload || !payload.length) return null
        return (
            <div style={{ background: 'var(--white)', border: '1px solid var(--gray)', borderRadius: 8, padding: '8px 12px', fontSize: 12 }}>
                <div style={{ fontWeight: 700, color: 'var(--navy)' }}>{payload[0]?.payload?.level}</div>
                <div style={{ color: 'var(--teal)' }}>{payload[0]?.value} profiles</div>
            </div>
        )
    }

    return (
        <div>
            <div className="page-header">
                <div>
                    <div className="page-title">Operations Dashboard</div>
                    <div className="page-subtitle">Real-time threat intelligence &amp; investigation overview</div>
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', textAlign: 'right' }}>
                    <div style={{ fontWeight: 600, color: 'var(--navy)' }}>{new Date().toLocaleDateString('en-IN', { weekday: 'long' })}</div>
                    {new Date().toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' })}
                </div>
            </div>

            {/* ── STAT CARDS ─────────────────────────────────────── */}
            <div className="stat-grid">
                {[
                    { label: 'Total Cases', value: cases.length, sub: `${openCases} active`, icon: '📁' },
                    { label: 'Flagged Profiles', value: flagged, sub: 'on blacklist', icon: '🚨' },
                    { label: 'Profiles Analyzed', value: totalProfiles, sub: 'across all cases', icon: '🔍' },
                    { label: 'Evidence Anchored', value: totalEvidence, sub: 'blockchain-verified', icon: '⛓️' },
                ].map(s => (
                    <div key={s.label} className="stat-card">
                        <div style={{ fontSize: 24, position: 'absolute', right: 18, top: 20, opacity: .1 }}>{s.icon}</div>
                        <div className="stat-label">{s.label}</div>
                        <div className="stat-value">{s.value}</div>
                        <div className="stat-sub">{s.sub}</div>
                    </div>
                ))}
            </div>

            {/* ── ROW 2 ──────────────────────────────────────────── */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.6fr 1fr', gap: 18, marginBottom: 18 }}>
                {/* Risk Gauge */}
                <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 16, minHeight: 260 }}>
                    <div className="card-title" style={{ width: '100%' }}>TOP RISK SCORE</div>
                    <CircularGauge value={(blacklist || []).reduce((m: number, p: any) => Math.max(m, p.risk_score || 0), 0)} label="Highest Active Score" />
                    <div style={{ display: 'flex', gap: 12, fontSize: 11 }}>
                        {['Critical', 'High', 'Medium', 'Low'].map((l, i) => (
                            <div key={l} style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--text-muted)' }}>
                                <div style={{ width: 8, height: 8, borderRadius: '50%', background: Object.values(RISK_COLORS)[i] }} />
                                {l}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Risk Chart */}
                <div className="card">
                    <div className="card-title">RISK DISTRIBUTION</div>
                    <ResponsiveContainer width="100%" height={180}>
                        <BarChart data={riskDist} margin={{ top: 0, right: 10, bottom: 0, left: -20 }}>
                            <XAxis dataKey="level" tick={{ fill: '#6B7FA3', fontSize: 11 }} axisLine={false} tickLine={false} />
                            <YAxis tick={{ fill: '#6B7FA3', fontSize: 11 }} axisLine={false} tickLine={false} />
                            <Tooltip content={<CustomTooltip />} />
                            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                                {riskDist.map((e, i) => <Cell key={i} fill={e.color} />)}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                {/* Blockchain Status */}
                <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    <div className="card-title">LEDGER STATUS</div>
                    {[
                        { label: 'Blockchain Adapter', status: 'Online', green: true },
                        { label: 'Evidence Anchoring', status: 'Active', green: true },
                        { label: 'MinIO Storage', status: 'Connected', green: true },
                        { label: 'AI Scoring Engine', status: 'Ready', green: true },
                    ].map(s => (
                        <div key={s.label} className="data-pill">
                            <span className="data-pill-label">{s.label}</span>
                            <span style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12, fontWeight: 600, color: s.green ? 'var(--success)' : 'var(--danger)' }}>
                                <div className={`status-dot ${s.green ? 'dot-green' : 'dot-red'}`} />
                                {s.status}
                            </span>
                        </div>
                    ))}
                </div>
            </div>

            {/* ── Network Graph ──────────────────────────────────── */}
            <div className="card" style={{ marginBottom: 18 }}>
                <div className="card-title">BOT CLUSTER NETWORK GRAPH <span style={{ color: 'var(--text-muted)', fontWeight: 400, fontSize: 11, textTransform: 'none', letterSpacing: 0 }}>— Teal edges = bot cluster connections</span></div>
                <NetworkGraph />
            </div>

            {/* ── Recent Activity ────────────────────────────────── */}
            <div className="card">
                <div className="card-title">RECENT ACTIVITY</div>
                <div className="table-wrap">
                    <table>
                        <thead><tr><th>Case</th><th>Type</th><th>Unit</th><th>Status</th><th>Risk</th><th>Time</th></tr></thead>
                        <tbody>
                            {cases.slice(0, 6).map(c => (
                                <tr key={c.id}>
                                    <td style={{ fontWeight: 600, color: 'var(--navy)' }}>{c.title}</td>
                                    <td><span className="badge badge-teal">INVESTIGATION</span></td>
                                    <td style={{ color: 'var(--text-muted)' }}>{c.owner_unit || '—'}</td>
                                    <td><span className={`badge badge-${c.status.toLowerCase()}`}>{c.status}</span></td>
                                    <td>
                                        <div style={{ width: 80 }}><div className="risk-bar-wrap"><div className="risk-bar medium" style={{ width: '45%' }} /></div></div>
                                    </td>
                                    <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>{formatDistanceToNow(new Date(c.created_at), { addSuffix: true })}</td>
                                </tr>
                            ))}
                            {cases.length === 0 && <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 32 }}>No active investigations. Create your first case.</td></tr>}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}
