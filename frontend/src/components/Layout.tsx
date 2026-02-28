import { Outlet, NavLink, useNavigate } from 'react-router-dom'

const NAV = [
    { to: '/', label: 'Dashboard', exact: true, icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" /><rect x="14" y="14" width="7" height="7" /><rect x="3" y="14" width="7" height="7" /></svg> },
    { to: '/cases', label: 'Cases', icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" /></svg> },
    { to: '/analyze', label: 'Analyze Profile', icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg> },
    { to: '/evidence', label: 'Evidence Registry', icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" /></svg> },
    { to: '/registry', label: 'Blacklist', icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><line x1="4.93" y1="4.93" x2="19.07" y2="19.07" /></svg> },
    { to: '/reports', label: 'Reports', icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /></svg> },
    { to: '/settings', label: 'Settings', icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" /></svg> },
]

const decodeJwt = (token: string) => { try { return JSON.parse(atob(token.split('.')[1])) } catch { return {} } }

export default function Layout() {
    const navigate = useNavigate()
    const token = localStorage.getItem('token') || ''
    const payload = decodeJwt(token)
    const username = payload.username || 'Investigator'
    const role = payload.role || 'USER'
    const initials = username.slice(0, 2).toUpperCase()

    const logout = () => { localStorage.removeItem('token'); navigate('/login') }

    return (
        <div className="layout">
            {/* ── SIDEBAR ───────────────────────────────────────── */}
            <nav className="sidebar">
                <div className="sidebar-logo">
                    <div className="logo-badge">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0A1F44" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                        </svg>
                    </div>
                    <div>
                        <div className="logo-name">AUTHENTIX</div>
                        <div className="logo-sub">LEDGER</div>
                    </div>
                </div>

                <div className="sidebar-nav">
                    <div className="nav-section-label">Investigation</div>
                    {NAV.filter(n => ['/', 'cases', '/cases', '/analyze', '/evidence'].some(p => n.to === p || n.to.startsWith('/analyze') || n.to.startsWith('/evidence'))).slice(0, 4).map(({ to, label, icon, exact }) => (
                        <NavLink key={to} to={to} end={exact} className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
                            {icon}{label}
                        </NavLink>
                    ))}
                    <div className="nav-section-label" style={{ marginTop: 8 }}>Intel</div>
                    {NAV.slice(4).map(({ to, label, icon, exact }) => (
                        <NavLink key={to} to={to} end={exact} className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
                            {icon}{label}
                        </NavLink>
                    ))}
                </div>

                <div className="sidebar-footer">
                    <div className="sidebar-user">
                        <div className="user-avatar">{initials}</div>
                        <div>
                            <div className="user-name">{username}</div>
                            <div className="user-role">{role}</div>
                        </div>
                    </div>
                    <button className="btn btn-outline-white btn-sm" style={{ width: '100%', justifyContent: 'center' }} onClick={logout}>
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" /></svg>
                        Sign Out
                    </button>
                </div>
            </nav>

            {/* ── MAIN ─────────────────────────────────────────── */}
            <div className="main-wrapper">
                <header className="header">
                    <div className="header-page-title">Operations Centre</div>
                    <div className="search-wrap">
                        <svg className="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg>
                        <input className="header-search" placeholder="Search cases, hashes, profiles…" />
                    </div>
                    <div className="header-right">
                        <button style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'rgba(255,255,255,.5)', position: 'relative', padding: 6 }}>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 0 1-3.46 0" /></svg>
                            <span style={{ position: 'absolute', top: 4, right: 4, width: 7, height: 7, borderRadius: '50%', background: 'var(--teal)', border: '1.5px solid var(--navy)' }} />
                        </button>
                        <button className="btn btn-primary btn-sm" onClick={() => navigate('/cases')}>
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>
                            New Case
                        </button>
                    </div>
                </header>
                <main className="main-content"><Outlet /></main>
            </div>
        </div>
    )
}
