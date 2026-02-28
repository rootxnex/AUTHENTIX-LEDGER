package main

// Event emission helpers for write transactions.
// Events are emitted on every state-changing transaction for downstream subscribers.

import (
	"encoding/json"
	"fmt"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// emitEvent serializes payload to JSON and sets Fabric event.
func emitEvent(ctx contractapi.TransactionContextInterface, eventName string, payload interface{}) error {
	data, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("failed to serialize event payload: %w", err)
	}
	return ctx.GetStub().SetEvent(eventName, data)
}

// ── Event Payload Types ────────────────────────────────────────────────────────

type CaseCreatedEvent struct {
	CaseID    string `json:"caseId"`
	OwnerUnit string `json:"ownerUnit"`
	CreatedBy string `json:"createdBy"`
	CreatedAt string `json:"createdAt"`
}

type ProfileRegisteredEvent struct {
	ProfileHash      string  `json:"profileHash"`
	Platform         string  `json:"platform"`
	RiskScoreSummary float64 `json:"riskScoreSummary"`
	Status           string  `json:"status"`
	CreatedBy        string  `json:"createdBy"`
	CreatedAt        string  `json:"createdAt"`
}

type EvidenceAddedEvent struct {
	EvidenceHash string `json:"evidenceHash"`
	CaseID       string `json:"caseId"`
	ProfileHash  string `json:"profileHash"`
	EvidenceType string `json:"evidenceType"`
	CreatedBy    string `json:"createdBy"`
	CreatedAt    string `json:"createdAt"`
}

type CaseStatusUpdatedEvent struct {
	CaseID    string `json:"caseId"`
	NewStatus string `json:"newStatus"`
	UpdatedBy string `json:"updatedBy"`
	UpdatedAt string `json:"updatedAt"`
}

type ProfileStatusUpdatedEvent struct {
	ProfileHash string `json:"profileHash"`
	NewStatus   string `json:"newStatus"`
	UpdatedBy   string `json:"updatedBy"`
	UpdatedAt   string `json:"updatedAt"`
}
