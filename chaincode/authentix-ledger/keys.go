package main

// Composite key builders — ensures consistent, queryable state keys.

import (
	"fmt"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

const (
	keyCasePrefix            = "case"
	keyProfilePrefix         = "profile"
	keyEvidencePrefix        = "evidence"
	keyEvidenceByProfilePfx  = "evidenceByProfile"
)

// caseKey: case~{ownerUnit}~{caseId}
func caseKey(ctx contractapi.TransactionContextInterface, ownerUnit, caseID string) (string, error) {
	return ctx.GetStub().CreateCompositeKey(keyCasePrefix, []string{ownerUnit, caseID})
}

// profileKey: profile~{platform}~{profileHash}
func profileKey(ctx contractapi.TransactionContextInterface, platform, profileHash string) (string, error) {
	return ctx.GetStub().CreateCompositeKey(keyProfilePrefix, []string{platform, profileHash})
}

// evidenceKey: evidence~{caseId}~{evidenceHash}
func evidenceKey(ctx contractapi.TransactionContextInterface, caseID, evidenceHash string) (string, error) {
	return ctx.GetStub().CreateCompositeKey(keyEvidencePrefix, []string{caseID, evidenceHash})
}

// evidenceByProfileKey: evidenceByProfile~{profileHash}~{evidenceHash}
func evidenceByProfileKey(ctx contractapi.TransactionContextInterface, profileHash, evidenceHash string) (string, error) {
	return ctx.GetStub().CreateCompositeKey(keyEvidenceByProfilePfx, []string{profileHash, evidenceHash})
}

// validateNonEmpty checks that required fields are not blank.
func validateNonEmpty(fields map[string]string) error {
	for name, val := range fields {
		if val == "" {
			return fmt.Errorf("validation error: field '%s' must not be empty", name)
		}
	}
	return nil
}
