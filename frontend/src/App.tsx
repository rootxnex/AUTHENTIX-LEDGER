import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/Login'
import DashboardPage from './pages/Dashboard'
import CasesPage from './pages/Cases'
import AnalyzePage from './pages/Analyze'
import EvidencePage from './pages/Evidence'
import RegistryPage from './pages/Registry'
import ReportsPage from './pages/Reports'
import Layout from './components/Layout'

function isAuthenticated() {
    return !!localStorage.getItem('token')
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
    return isAuthenticated() ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
                    <Route index element={<DashboardPage />} />
                    <Route path="cases" element={<CasesPage />} />
                    <Route path="analyze" element={<AnalyzePage />} />
                    <Route path="evidence/:caseId?" element={<EvidencePage />} />
                    <Route path="registry" element={<RegistryPage />} />
                    <Route path="reports/:caseId?" element={<ReportsPage />} />
                </Route>
            </Routes>
        </BrowserRouter>
    )
}
