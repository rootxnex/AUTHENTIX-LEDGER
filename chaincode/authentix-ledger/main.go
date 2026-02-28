package main

// Chaincode entrypoint.

import (
	"log"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// AuthentixContract is the main smart contract struct.
type AuthentixContract struct {
	contractapi.Contract
}

func main() {
	cc, err := contractapi.NewChaincode(&AuthentixContract{})
	if err != nil {
		log.Panicf("Error creating authentix-ledger chaincode: %v", err)
	}
	if err = cc.Start(); err != nil {
		log.Panicf("Error starting authentix-ledger chaincode: %v", err)
	}
}
