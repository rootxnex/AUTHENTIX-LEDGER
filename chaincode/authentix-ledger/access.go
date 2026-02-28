package main

// RBAC enforcement using Hyperledger Fabric Client Identity.
// Reads the role from the client's X.509 certificate attribute "role".
// Required MSP attribute: role=ADMIN|INVESTIGATOR|AUDITOR

import (
	"fmt"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

const roleAttribute = "role"

// getClientRole reads the "role" attribute from the client identity certificate.
func getClientRole(ctx contractapi.TransactionContextInterface) (UserRole, error) {
	id := ctx.GetClientIdentity()
	roleVal, found, err := id.GetAttributeValue(roleAttribute)
	if err != nil {
		return "", fmt.Errorf("failed to read role attribute: %w", err)
	}
	if !found {
		return "", fmt.Errorf("role attribute not found in certificate; contact your MSP admin")
	}
	role := UserRole(roleVal)
	switch role {
	case RoleAdmin, RoleInvestigator, RoleAuditor:
		return role, nil
	default:
		return "", fmt.Errorf("unknown role '%s': must be ADMIN, INVESTIGATOR, or AUDITOR", roleVal)
	}
}

// getClientID returns a stable operator identifier (MSPID + SubjectDN).
func getClientID(ctx contractapi.TransactionContextInterface) (string, error) {
	id := ctx.GetClientIdentity()
	mspID, err := id.GetMSPID()
	if err != nil {
		return "", fmt.Errorf("failed to get MSPID: %w", err)
	}
	cert, err := id.GetX509Certificate()
	if err != nil {
		return "", fmt.Errorf("failed to get certificate: %w", err)
	}
	return fmt.Sprintf("%s::%s", mspID, cert.Subject.CommonName), nil
}

// requireWriteAccess asserts caller has ADMIN or INVESTIGATOR role.
func requireWriteAccess(ctx contractapi.TransactionContextInterface) error {
	role, err := getClientRole(ctx)
	if err != nil {
		return err
	}
	if role != RoleAdmin && role != RoleInvestigator {
		return fmt.Errorf("access denied: write operations require ADMIN or INVESTIGATOR role, got '%s'", role)
	}
	return nil
}

// requireReadAccess asserts caller has any valid role (ADMIN, INVESTIGATOR, AUDITOR).
func requireReadAccess(ctx contractapi.TransactionContextInterface) error {
	_, err := getClientRole(ctx)
	return err
}

// requireAdminAccess asserts ADMIN only.
func requireAdminAccess(ctx contractapi.TransactionContextInterface) error {
	role, err := getClientRole(ctx)
	if err != nil {
		return err
	}
	if role != RoleAdmin {
		return fmt.Errorf("access denied: admin-only operation, got '%s'", role)
	}
	return nil
}
