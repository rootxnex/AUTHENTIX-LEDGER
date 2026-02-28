package main

// Evidence management transactions.

import (
	"encoding/json"
	"fmt"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// AddEvidence anchors an evidence hash. Write access required.
// evidenceHash = SHA-256 of evidence bundle (never raw evidence content).
// storagePointer = opaque MinIO key (not a URL — prevents direct access).
func (c *AuthentixContract) AddEvidence(
	ctx contractapi.TransactionContextInterface,
	evidenceHash, caseID, profileHash, evidenceTypeStr, storagePointer string,
) error {
	if err := requireWriteAccess(ctx); err != nil {
		return err
	}
	if err := validateNonEmpty(map[string]string{
		"evidenceHash": evidenceHash, "caseId": caseID,
		"evidenceType": evidenceTypeStr, "storagePointer": storagePointer,
	}); err != nil {
		return err
	}

	evidenceType := EvidenceType(evidenceTypeStr)
	switch evidenceType {
	case EvidenceScreenshot, EvidenceJSONExport, EvidenceReport, EvidenceOther:
	default:
		return fmt.Errorf("invalid evidenceType '%s'", evidenceTypeStr)
	}

	// Primary key: evidence~{caseId}~{evidenceHash}
	key, err := evidenceKey(ctx, caseID, evidenceHash)
	if err != nil {
		return err
	}
	// Idempotency: reject duplicate evidence
	existing, err := ctx.GetStub().GetState(key)
	if err != nil {
		return fmt.Errorf("state read error: %w", err)
	}
	if existing != nil {
		return fmt.Errorf("evidence hash '%s' already anchored on ledger", evidenceHash)
	}

	clientID, _ := getClientID(ctx)
	now := currentTime()

	record := EvidenceRecord{
		DocType:        "EvidenceRecord",
		EvidenceHash:   evidenceHash,
		CaseID:         caseID,
		ProfileHash:    profileHash,
		EvidenceType:   evidenceType,
		StoragePointer: storagePointer,
		CreatedAt:      now,
		CreatedBy:      clientID,
	}

	data, err := json.Marshal(record)
	if err != nil {
		return err
	}
	if err = ctx.GetStub().PutState(key, data); err != nil {
		return err
	}

	// Secondary index: evidenceByProfile~{profileHash}~{evidenceHash}
	if profileHash != "" {
		idx, err := evidenceByProfileKey(ctx, profileHash, evidenceHash)
		if err != nil {
			return err
		}
		// Value is a pointer to the primary key (composite key trick)
		if err = ctx.GetStub().PutState(idx, []byte(key)); err != nil {
			return err
		}
	}

	return emitEvent(ctx, "EvidenceAdded", EvidenceAddedEvent{
		EvidenceHash: evidenceHash, CaseID: caseID, ProfileHash: profileHash,
		EvidenceType: evidenceTypeStr, CreatedBy: clientID, CreatedAt: now,
	})
}

// VerifyEvidenceHash checks if an evidence hash is on the ledger (chain-of-custody check).
// AUDITOR-accessible.
func (c *AuthentixContract) VerifyEvidenceHash(
	ctx contractapi.TransactionContextInterface,
	caseID, evidenceHash string,
) (bool, error) {
	if err := requireReadAccess(ctx); err != nil {
		return false, err
	}

	key, err := evidenceKey(ctx, caseID, evidenceHash)
	if err != nil {
		return false, err
	}
	data, err := ctx.GetStub().GetState(key)
	if err != nil {
		return false, err
	}
	return data != nil, nil
}

// GetEvidence retrieves an EvidenceRecord by caseID + evidenceHash.
func (c *AuthentixContract) GetEvidence(
	ctx contractapi.TransactionContextInterface,
	caseID, evidenceHash string,
) (*EvidenceRecord, error) {
	if err := requireReadAccess(ctx); err != nil {
		return nil, err
	}

	key, err := evidenceKey(ctx, caseID, evidenceHash)
	if err != nil {
		return nil, err
	}
	data, err := ctx.GetStub().GetState(key)
	if err != nil || data == nil {
		return nil, fmt.Errorf("evidence hash '%s' not found in case '%s'", evidenceHash, caseID)
	}

	var record EvidenceRecord
	if err = json.Unmarshal(data, &record); err != nil {
		return nil, err
	}
	return &record, nil
}

// ListEvidenceByProfile returns all evidence hashes linked to a profile.
func (c *AuthentixContract) ListEvidenceByProfile(
	ctx contractapi.TransactionContextInterface,
	profileHash string,
) ([]*EvidenceRecord, error) {
	if err := requireReadAccess(ctx); err != nil {
		return nil, err
	}

	iter, err := ctx.GetStub().GetStateByPartialCompositeKey(keyEvidenceByProfilePfx, []string{profileHash})
	if err != nil {
		return nil, fmt.Errorf("index query failed: %w", err)
	}
	defer iter.Close()

	var records []*EvidenceRecord
	for iter.HasNext() {
		kv, err := iter.Next()
		if err != nil {
			return nil, err
		}
		// Value is the primary evidence key
		primaryKey := string(kv.Value)
		data, err := ctx.GetStub().GetState(primaryKey)
		if err != nil || data == nil {
			continue
		}
		var rec EvidenceRecord
		if err = json.Unmarshal(data, &rec); err == nil {
			records = append(records, &rec)
		}
	}
	return records, nil
}
