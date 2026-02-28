package main

// Data models for AUTHENTIX LEDGER chaincode.
// All structs use deterministic JSON (sorted keys via json.Marshal + sorted field names).

import "time"

// ── Enumerations ──────────────────────────────────────────────────────────────

type ProfileStatus string

const (
	ProfilePending   ProfileStatus = "PENDING"
	ProfileFlagged   ProfileStatus = "FLAGGED"
	ProfileVerified  ProfileStatus = "VERIFIED"
	ProfileDismissed ProfileStatus = "DISMISSED"
)

type CaseStatus string

const (
	CaseOpen   CaseStatus = "OPEN"
	CaseClosed CaseStatus = "CLOSED"
)

type EvidenceType string

const (
	EvidenceScreenshot EvidenceType = "SCREENSHOT"
	EvidenceJSONExport EvidenceType = "JSON_EXPORT"
	EvidenceReport     EvidenceType = "REPORT"
	EvidenceOther      EvidenceType = "OTHER"
)

type UserRole string

const (
	RoleAdmin        UserRole = "ADMIN"
	RoleInvestigator UserRole = "INVESTIGATOR"
	RoleAuditor      UserRole = "AUDITOR"
)

// ── ProfileRecord ─────────────────────────────────────────────────────────────

// ProfileRecord anchors a social media profile's SHA-256 hash on the ledger.
// PII is never stored here — only the hash.
type ProfileRecord struct {
	DocType          string        `json:"docType"`         // "ProfileRecord" — for CouchDB queries
	ProfileHash      string        `json:"profileHash"`     // SHA-256 of canonical profile ID
	Platform         string        `json:"platform"`        // twitter|instagram|facebook|...
	Status           ProfileStatus `json:"status"`
	RiskScoreSummary float64       `json:"riskScoreSummary"` // 0–100
	CreatedAt        string        `json:"createdAt"`        // RFC3339 UTC
	UpdatedAt        string        `json:"updatedAt"`
	CreatedBy        string        `json:"createdBy"`        // investigatorId
	CaseID           string        `json:"caseId"`
}

// ── EvidenceRecord ────────────────────────────────────────────────────────────

// EvidenceRecord anchors an encrypted evidence bundle's SHA-256 hash on the ledger.
// The storagePointer is an opaque reference (MinIO object key), NOT a URL.
type EvidenceRecord struct {
	DocType        string       `json:"docType"`        // "EvidenceRecord"
	EvidenceHash   string       `json:"evidenceHash"`   // SHA-256 of evidence bundle
	CaseID         string       `json:"caseId"`
	ProfileHash    string       `json:"profileHash"`    // may be empty
	EvidenceType   EvidenceType `json:"evidenceType"`
	StoragePointer string       `json:"storagePointer"` // opaque MinIO key
	CreatedAt      string       `json:"createdAt"`
	CreatedBy      string       `json:"createdBy"`
}

// ── CaseRecord ────────────────────────────────────────────────────────────────

type CaseRecord struct {
	DocType     string     `json:"docType"`    // "CaseRecord"
	CaseID      string     `json:"caseId"`
	Title       string     `json:"title"`
	Description string     `json:"description"`
	OwnerUnit   string     `json:"ownerUnit"`
	Status      CaseStatus `json:"status"`
	CreatedAt   string     `json:"createdAt"`
	UpdatedAt   string     `json:"updatedAt"`
	CreatedBy   string     `json:"createdBy"`
}

// ── Helper ────────────────────────────────────────────────────────────────────

func currentTime() string {
	return time.Now().UTC().Format(time.RFC3339)
}
