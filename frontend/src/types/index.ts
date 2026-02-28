export interface TokenPayload {
    access_token: string
    token_type: string
    role: string
    username: string
}

export interface User {
    id: string
    username: string
    email: string
    full_name?: string
    role: 'ADMIN' | 'INVESTIGATOR' | 'AUDITOR'
    unit?: string
    is_active: boolean
    created_at: string
}

export interface Case {
    id: string
    title: string
    description?: string
    fir_number?: string
    owner_unit: string
    status: 'OPEN' | 'CLOSED' | 'ARCHIVED'
    created_at: string
    updated_at: string
    owner_id: string
    blockchain_tx_id?: string
    profile_count: number
    evidence_count: number
}

export interface RiskFactor {
    name: string
    contribution: number
    direction: 'increases_risk' | 'decreases_risk'
    description: string
}

export interface ProfileAnalysis {
    profile_hash: string
    profile_url: string
    platform: string
    risk_score: number
    risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
    risk_factors: RiskFactor[]
    status: string
    blockchain_tx_id?: string
    record_id: string
    analyzed_at: string
}

export interface ProfileRecord {
    id: string
    profile_hash: string
    profile_url: string
    platform: string
    status: string
    risk_score?: number
    risk_factors?: string
    case_id: string
    created_at: string
    blockchain_tx_id?: string
}

export interface EvidenceRecord {
    id: string
    evidence_hash: string
    original_filename: string
    evidence_type: string
    file_size_bytes?: number
    mime_type?: string
    case_id: string
    profile_id?: string
    created_at: string
    blockchain_tx_id?: string
}

export interface RegistryResult {
    hash: string
    hash_type: string
    found: boolean
    records: object[]
}

export interface Report {
    report_id: string
    case_id: string
    generated_at: string
    download_url: string
    hash_proof: string
}
