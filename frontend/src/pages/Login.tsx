import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../api/client'

export default function LoginPage() {
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const navigate = useNavigate()

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault(); setError(''); setLoading(true)
        try {
            const res = await authApi.login(username, password)
            localStorage.setItem('token', res.data.access_token)
            navigate('/')
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Authentication failed. Verify your credentials.')
        } finally { setLoading(false) }
    }

    return (
        <div style={{ minHeight: '100vh', background: 'var(--navy)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
            {/* Top bar */}
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, background: 'var(--teal)' }} />

            {/* Logo mark */}
            <div style={{ textAlign: 'center', marginBottom: 36 }}>
                <div style={{ width: 60, height: 60, borderRadius: 14, background: 'var(--teal)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
                    <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#0A1F44" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                    </svg>
                </div>
                <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--white)', letterSpacing: '.06em' }}>AUTHENTIX LEDGER</div>
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,.35)', marginTop: 5, letterSpacing: '.1em', textTransform: 'uppercase' }}>
                    Blockchain Investigation Platform · Restricted Access
                </div>
            </div>

            {/* Card */}
            <div style={{ background: 'var(--white)', borderRadius: 'var(--radius)', padding: '32px 36px', width: 420, boxShadow: 'var(--shadow-lg)' }}>
                <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--navy)', marginBottom: 4 }}>Secure Sign In</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 24 }}>Authorised personnel only. All access is audited.</div>

                {error && (
                    <div className="alert alert-error" style={{ marginBottom: 16 }}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></svg>
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label className="form-label">Badge ID / Username</label>
                        <div className="input-icon-wrap">
                            <svg className="input-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
                            <input id="username-input" className="form-input has-icon" type="text" placeholder="e.g. INV-MH-2024" value={username} onChange={e => setUsername(e.target.value)} required />
                        </div>
                    </div>
                    <div className="form-group" style={{ marginBottom: 24 }}>
                        <label className="form-label">Passphrase</label>
                        <div className="input-icon-wrap">
                            <svg className="input-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
                            <input id="password-input" className="form-input has-icon" type="password" placeholder="Enter passphrase" value={password} onChange={e => setPassword(e.target.value)} required />
                        </div>
                    </div>
                    <button id="login-btn" type="submit" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', padding: '12px', fontSize: 14 }} disabled={loading}>
                        {loading ? <><div className="spinner spinner-navy" style={{ width: 15, height: 15 }} /> Authenticating…</> : 'Authenticate & Enter'}
                    </button>
                </form>
            </div>

            {/* Footer */}
            <div style={{ marginTop: 24, fontSize: 11, color: 'rgba(255,255,255,.2)', textAlign: 'center', lineHeight: 1.7 }}>
                Compliant with IT Act 2000 &nbsp;·&nbsp; Section 65B Evidence Act &nbsp;·&nbsp; DPDP Act 2023<br />
                Unauthorized access is a criminal offence under Sec. 66 IT Act
            </div>
        </div>
    )
}
