"""
Victor Synthetic Orchestrator
Unified autonomous super-intelligent agent orchestrating the MASSIVEMAGNETICS AI ecosystem.
"""

__version__ = "1.1.0"
__author__ = "MASSIVEMAGNETICS"

from .core import VictorOrchestrator
from .agent import BaseAgent, AgentStatus
from .registry import ModuleRegistry
from .mesh import (
    CapabilityLease,
    ExecutionMesh,
    Receipt,
    SQLiteLedger,
    WorkOrder,
    WorkStatus,
    evidence_verifier,
)

__all__ = [
    "VictorOrchestrator",
    "BaseAgent",
    "AgentStatus",
    "ModuleRegistry",
    "CapabilityLease",
    "ExecutionMesh",
    "Receipt",
    "SQLiteLedger",
    "WorkOrder",
    "WorkStatus",
    "evidence_verifier",
]
