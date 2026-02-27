"""
Blockchain Adapter — Interface + Mock Implementation + Fabric Stub.

Architecture decision:
  - AbstractBlockchainAdapter defines the interface.
  - MockBlockchainAdapter implements in-memory ledger (demo/hackathon).
  - FabricBlockchainAdapter is a stub with TODO markers for real Fabric Gateway SDK.
  - get_blockchain_adapter() factory reads BLOCKCHAIN_MODE from settings.
"""
import uuid
import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)


# ── Abstract Interface ────────────────────────────────────────────────────────

class AbstractBlockchainAdapter(ABC):

    @abstractmethod
    async def create_case(self, case_id: str, title: str, owner_unit: str, created_by: str) -> str:
        """Anchor a new case. Returns transaction ID."""

    @abstractmethod
    async def update_case_status(self, case_id: str, status: str, updated_by: str) -> str:
        """Update case status on ledger."""

    @abstractmethod
    async def register_profile(
        self, profile_hash: str, platform: str, risk_score: float,
        case_id: str, created_by: str,
    ) -> str:
        """Register a profile hash on ledger. Returns tx ID."""

    @abstractmethod
    async def update_profile_status(self, profile_hash: str, status: str, updated_by: str) -> str:
        """Update profile status."""

    @abstractmethod
    async def add_evidence(
        self, evidence_hash: str, case_id: str, profile_hash: Optional[str],
        evidence_type: str, storage_pointer: str, created_by: str,
    ) -> str:
        """Anchor evidence hash. Returns tx ID."""

    @abstractmethod
    async def verify_evidence_hash(self, evidence_hash: str) -> dict:
        """Verify evidence hash exists. Returns metadata dict."""

    @abstractmethod
    async def get_profile_history(self, profile_hash: str) -> list:
        """Get full ledger history for a profile hash."""


# ── Mock Implementation (In-Memory) ──────────────────────────────────────────

class _MockLedger:
    """In-process singleton that mimics a simple ledger."""
    def __init__(self):
        self.cases: dict[str, dict] = {}
        self.profiles: dict[str, list[dict]] = {}  # hash -> list of states
        self.evidence: dict[str, dict] = {}  # evidence_hash -> metadata

    def new_tx_id(self) -> str:
        return f"MOCK-TX-{uuid.uuid4().hex[:16].upper()}"

    def now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


_ledger = _MockLedger()


class MockBlockchainAdapter(AbstractBlockchainAdapter):

    async def create_case(self, case_id: str, title: str, owner_unit: str, created_by: str) -> str:
        tx = _ledger.new_tx_id()
        _ledger.cases[case_id] = {
            "caseId": case_id, "title": title, "ownerUnit": owner_unit,
            "status": "OPEN", "createdBy": created_by,
            "createdAt": _ledger.now(), "txId": tx,
        }
        logger.info("mock_chain.case_created", case_id=case_id, tx=tx)
        return tx

    async def update_case_status(self, case_id: str, status: str, updated_by: str) -> str:
        tx = _ledger.new_tx_id()
        if case_id in _ledger.cases:
            _ledger.cases[case_id]["status"] = status
            _ledger.cases[case_id]["updatedBy"] = updated_by
        logger.info("mock_chain.case_status_updated", case_id=case_id, status=status, tx=tx)
        return tx

    async def register_profile(
        self, profile_hash: str, platform: str, risk_score: float,
        case_id: str, created_by: str,
    ) -> str:
        tx = _ledger.new_tx_id()
        entry = {
            "profileHash": profile_hash, "platform": platform,
            "riskScore": risk_score, "caseId": case_id,
            "status": "PENDING", "createdBy": created_by,
            "createdAt": _ledger.now(), "txId": tx,
        }
        _ledger.profiles.setdefault(profile_hash, []).append(entry)
        logger.info("mock_chain.profile_registered", profile_hash=profile_hash, tx=tx)
        return tx

    async def update_profile_status(self, profile_hash: str, status: str, updated_by: str) -> str:
        tx = _ledger.new_tx_id()
        if profile_hash in _ledger.profiles:
            _ledger.profiles[profile_hash][-1]["status"] = status
        logger.info("mock_chain.profile_status", profile_hash=profile_hash, status=status, tx=tx)
        return tx

    async def add_evidence(
        self, evidence_hash: str, case_id: str, profile_hash: Optional[str],
        evidence_type: str, storage_pointer: str, created_by: str,
    ) -> str:
        tx = _ledger.new_tx_id()
        _ledger.evidence[evidence_hash] = {
            "evidenceHash": evidence_hash, "caseId": case_id,
            "profileHash": profile_hash, "evidenceType": evidence_type,
            "storagePointer": storage_pointer, "createdBy": created_by,
            "createdAt": _ledger.now(), "txId": tx,
        }
        logger.info("mock_chain.evidence_added", evidence_hash=evidence_hash, tx=tx)
        return tx

    async def verify_evidence_hash(self, evidence_hash: str) -> dict:
        rec = _ledger.evidence.get(evidence_hash)
        if rec:
            return {"found": True, "metadata": rec}
        return {"found": False, "metadata": None}

    async def get_profile_history(self, profile_hash: str) -> list:
        return _ledger.profiles.get(profile_hash, [])


# ── Hyperledger Fabric Stub ───────────────────────────────────────────────────

class FabricBlockchainAdapter(AbstractBlockchainAdapter):
    """
    Production Hyperledger Fabric adapter using the Fabric Gateway SDK.
    Requires: pip install fabric-sdk-py  (or use fabric-gateway gRPC client)
    
    TODO: Replace all raise NotImplementedError with actual Fabric Gateway calls.
    Configure via settings.FABRIC_* environment variables.
    """

    def __init__(self):
        # TODO: Initialize Fabric Gateway connection
        # from fabric_sdk_py.gateway import Gateway
        # self.gateway = Gateway(...)
        # self.network = self.gateway.get_network(settings.FABRIC_CHANNEL)
        # self.contract = self.network.get_contract(settings.FABRIC_CHAINCODE)
        logger.warning("FabricBlockchainAdapter is a STUB — not connected to real Fabric network")

    async def create_case(self, case_id: str, title: str, owner_unit: str, created_by: str) -> str:
        # TODO: self.contract.submit_transaction("CreateCase", case_id, title, owner_unit, created_by)
        raise NotImplementedError("Fabric adapter: CreateCase not implemented")

    async def update_case_status(self, case_id: str, status: str, updated_by: str) -> str:
        # TODO: self.contract.submit_transaction("UpdateCaseStatus", case_id, status, updated_by)
        raise NotImplementedError("Fabric adapter: UpdateCaseStatus not implemented")

    async def register_profile(self, profile_hash, platform, risk_score, case_id, created_by) -> str:
        # TODO: self.contract.submit_transaction("RegisterProfile", profile_hash, platform, str(risk_score), case_id, created_by)
        raise NotImplementedError("Fabric adapter: RegisterProfile not implemented")

    async def update_profile_status(self, profile_hash, status, updated_by) -> str:
        # TODO: self.contract.submit_transaction("UpdateProfileStatus", profile_hash, status, updated_by)
        raise NotImplementedError("Fabric adapter: UpdateProfileStatus not implemented")

    async def add_evidence(self, evidence_hash, case_id, profile_hash, evidence_type, storage_pointer, created_by) -> str:
        # TODO: self.contract.submit_transaction("AddEvidence", evidence_hash, case_id, profile_hash or "", evidence_type, storage_pointer, created_by)
        raise NotImplementedError("Fabric adapter: AddEvidence not implemented")

    async def verify_evidence_hash(self, evidence_hash: str) -> dict:
        # TODO: result = self.contract.evaluate_transaction("VerifyEvidenceHash", evidence_hash)
        raise NotImplementedError("Fabric adapter: VerifyEvidenceHash not implemented")

    async def get_profile_history(self, profile_hash: str) -> list:
        # TODO: result = self.contract.evaluate_transaction("GetProfileHistory", profile_hash)
        raise NotImplementedError("Fabric adapter: GetProfileHistory not implemented")


# ── Factory ───────────────────────────────────────────────────────────────────

_adapter_cache: Optional[AbstractBlockchainAdapter] = None


def get_blockchain_adapter() -> AbstractBlockchainAdapter:
    global _adapter_cache
    if _adapter_cache is None:
        if settings.BLOCKCHAIN_MODE == "fabric":
            _adapter_cache = FabricBlockchainAdapter()
        else:
            _adapter_cache = MockBlockchainAdapter()
        logger.info("blockchain_adapter_initialized", mode=settings.BLOCKCHAIN_MODE)
    return _adapter_cache
