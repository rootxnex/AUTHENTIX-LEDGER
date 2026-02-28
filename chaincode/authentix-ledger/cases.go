package main

// Case management transactions.

import (
	"encoding/json"
	"fmt"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// CreateCase anchors a new investigation case on the ledger.
// Requires: ADMIN or INVESTIGATOR role.
// Args: caseId, title, description, ownerUnit
func (c *AuthentixContract) CreateCase(
	ctx contractapi.TransactionContextInterface,
	caseID, title, description, ownerUnit string,
) error {
	if err := requireWriteAccess(ctx); err != nil {
		return err
	}
	if err := validateNonEmpty(map[string]string{
		"caseId": caseID, "title": title, "ownerUnit": ownerUnit,
	}); err != nil {
		return err
	}

	// Idempotency: reject duplicate
	key, err := caseKey(ctx, ownerUnit, caseID)
	if err != nil {
		return fmt.Errorf("failed to build key: %w", err)
	}
	existing, err := ctx.GetStub().GetState(key)
	if err != nil {
		return fmt.Errorf("state read error: %w", err)
	}
	if existing != nil {
		return fmt.Errorf("case '%s' already exists", caseID)
	}

	clientID, _ := getClientID(ctx)
	now := currentTime()

	record := CaseRecord{
		DocType:     "CaseRecord",
		CaseID:      caseID,
		Title:       title,
		Description: description,
		OwnerUnit:   ownerUnit,
		Status:      CaseOpen,
		CreatedAt:   now,
		UpdatedAt:   now,
		CreatedBy:   clientID,
	}

	data, err := json.Marshal(record)
	if err != nil {
		return fmt.Errorf("marshal error: %w", err)
	}
	if err = ctx.GetStub().PutState(key, data); err != nil {
		return fmt.Errorf("state write error: %w", err)
	}

	return emitEvent(ctx, "CaseCreated", CaseCreatedEvent{
		CaseID: caseID, OwnerUnit: ownerUnit, CreatedBy: clientID, CreatedAt: now,
	})
}

// UpdateCaseStatus transitions a case status. Requires write access.
func (c *AuthentixContract) UpdateCaseStatus(
	ctx contractapi.TransactionContextInterface,
	caseID, ownerUnit, newStatus string,
) error {
	if err := requireWriteAccess(ctx); err != nil {
		return err
	}

	key, err := caseKey(ctx, ownerUnit, caseID)
	if err != nil {
		return err
	}
	data, err := ctx.GetStub().GetState(key)
	if err != nil || data == nil {
		return fmt.Errorf("case '%s' not found", caseID)
	}

	var record CaseRecord
	if err = json.Unmarshal(data, &record); err != nil {
		return fmt.Errorf("unmarshal error: %w", err)
	}

	status := CaseStatus(newStatus)
	if status != CaseOpen && status != CaseClosed {
		return fmt.Errorf("invalid status '%s': must be OPEN or CLOSED", newStatus)
	}

	clientID, _ := getClientID(ctx)
	record.Status = status
	record.UpdatedAt = currentTime()

	updated, _ := json.Marshal(record)
	if err = ctx.GetStub().PutState(key, updated); err != nil {
		return err
	}

	return emitEvent(ctx, "CaseStatusUpdated", CaseStatusUpdatedEvent{
		CaseID: caseID, NewStatus: newStatus, UpdatedBy: clientID, UpdatedAt: record.UpdatedAt,
	})
}

// GetCase retrieves a CaseRecord. Requires read access.
func (c *AuthentixContract) GetCase(
	ctx contractapi.TransactionContextInterface,
	caseID, ownerUnit string,
) (*CaseRecord, error) {
	if err := requireReadAccess(ctx); err != nil {
		return nil, err
	}

	key, err := caseKey(ctx, ownerUnit, caseID)
	if err != nil {
		return nil, err
	}
	data, err := ctx.GetStub().GetState(key)
	if err != nil || data == nil {
		return nil, fmt.Errorf("case '%s' not found", caseID)
	}

	var record CaseRecord
	if err = json.Unmarshal(data, &record); err != nil {
		return nil, err
	}
	return &record, nil
}
