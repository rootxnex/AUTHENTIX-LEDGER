package main

// Profile registry transactions.

import (
	"encoding/json"
	"fmt"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// RegisterProfile anchors a profile hash on the ledger. Write access required.
// profileHash must be the SHA-256 of the canonical profile ID (never raw PII).
func (c *AuthentixContract) RegisterProfile(
	ctx contractapi.TransactionContextInterface,
	profileHash, platform, caseID string,
	riskScore float64,
) error {
	if err := requireWriteAccess(ctx); err != nil {
		return err
	}
	if err := validateNonEmpty(map[string]string{
		"profileHash": profileHash, "platform": platform, "caseId": caseID,
	}); err != nil {
		return err
	}
	if riskScore < 0 || riskScore > 100 {
		return fmt.Errorf("riskScore must be in [0, 100], got %f", riskScore)
	}

	key, err := profileKey(ctx, platform, profileHash)
	if err != nil {
		return err
	}

	clientID, _ := getClientID(ctx)
	now := currentTime()

	// Determine initial status from risk score
	status := ProfilePending
	if riskScore >= 50 {
		status = ProfileFlagged
	}

	record := ProfileRecord{
		DocType:          "ProfileRecord",
		ProfileHash:      profileHash,
		Platform:         platform,
		Status:           status,
		RiskScoreSummary: riskScore,
		CreatedAt:        now,
		UpdatedAt:        now,
		CreatedBy:        clientID,
		CaseID:           caseID,
	}

	data, err := json.Marshal(record)
	if err != nil {
		return fmt.Errorf("marshal error: %w", err)
	}

	// Use PutState (upsert) — allows re-analysis updates
	if err = ctx.GetStub().PutState(key, data); err != nil {
		return fmt.Errorf("state write error: %w", err)
	}

	return emitEvent(ctx, "ProfileRegistered", ProfileRegisteredEvent{
		ProfileHash:      profileHash,
		Platform:         platform,
		RiskScoreSummary: riskScore,
		Status:           string(status),
		CreatedBy:        clientID,
		CreatedAt:        now,
	})
}

// UpdateProfileStatus changes a profile's investigation status.
func (c *AuthentixContract) UpdateProfileStatus(
	ctx contractapi.TransactionContextInterface,
	profileHash, platform, newStatus string,
) error {
	if err := requireWriteAccess(ctx); err != nil {
		return err
	}

	key, err := profileKey(ctx, platform, profileHash)
	if err != nil {
		return err
	}
	data, err := ctx.GetStub().GetState(key)
	if err != nil || data == nil {
		return fmt.Errorf("profile '%s' on platform '%s' not found", profileHash, platform)
	}

	var record ProfileRecord
	if err = json.Unmarshal(data, &record); err != nil {
		return err
	}

	status := ProfileStatus(newStatus)
	switch status {
	case ProfilePending, ProfileFlagged, ProfileVerified, ProfileDismissed:
	default:
		return fmt.Errorf("invalid status '%s'", newStatus)
	}

	clientID, _ := getClientID(ctx)
	record.Status = status
	record.UpdatedAt = currentTime()

	updated, _ := json.Marshal(record)
	if err = ctx.GetStub().PutState(key, updated); err != nil {
		return err
	}

	return emitEvent(ctx, "ProfileStatusUpdated", ProfileStatusUpdatedEvent{
		ProfileHash: profileHash, NewStatus: newStatus,
		UpdatedBy: clientID, UpdatedAt: record.UpdatedAt,
	})
}

// GetProfile retrieves a ProfileRecord. Read access required.
func (c *AuthentixContract) GetProfile(
	ctx contractapi.TransactionContextInterface,
	profileHash, platform string,
) (*ProfileRecord, error) {
	if err := requireReadAccess(ctx); err != nil {
		return nil, err
	}

	key, err := profileKey(ctx, platform, profileHash)
	if err != nil {
		return nil, err
	}
	data, err := ctx.GetStub().GetState(key)
	if err != nil || data == nil {
		return nil, fmt.Errorf("profile '%s' not found", profileHash)
	}

	var record ProfileRecord
	if err = json.Unmarshal(data, &record); err != nil {
		return nil, err
	}
	return &record, nil
}

// GetProfileHistory returns the full ledger history for a profile hash (audit trail).
func (c *AuthentixContract) GetProfileHistory(
	ctx contractapi.TransactionContextInterface,
	profileHash, platform string,
) ([]map[string]interface{}, error) {
	if err := requireReadAccess(ctx); err != nil {
		return nil, err
	}

	key, err := profileKey(ctx, platform, profileHash)
	if err != nil {
		return nil, err
	}

	iter, err := ctx.GetStub().GetHistoryForKey(key)
	if err != nil {
		return nil, fmt.Errorf("history query failed: %w", err)
	}
	defer iter.Close()

	var history []map[string]interface{}
	for iter.HasNext() {
		mod, err := iter.Next()
		if err != nil {
			return nil, err
		}
		entry := map[string]interface{}{
			"txId":      mod.TxId,
			"timestamp": mod.Timestamp.AsTime().UTC().Format("2006-01-02T15:04:05Z"),
			"isDelete":  mod.IsDelete,
		}
		if !mod.IsDelete {
			var record ProfileRecord
			if err = json.Unmarshal(mod.Value, &record); err == nil {
				entry["value"] = record
			}
		}
		history = append(history, entry)
	}
	return history, nil
}
