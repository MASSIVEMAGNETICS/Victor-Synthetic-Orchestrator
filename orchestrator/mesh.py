"""Victor Execution Mesh v0.1.

Durable, bounded, evidence-gated parallel execution for Victor.
Standard-library only; designed to layer onto the existing orchestrator.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import sqlite3
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple, Union


class WorkStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class CapabilityLease:
    worker_type: str
    allowed: Tuple[str, ...]
    issued_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    lease_id: str = field(default_factory=lambda: f"lease_{uuid.uuid4().hex}")

    def permits(self, required: Iterable[str], now: Optional[float] = None) -> bool:
        current = time.time() if now is None else now
        if self.expires_at is not None and current >= self.expires_at:
            return False
        allowed = set(self.allowed)
        return set(required).issubset(allowed)


@dataclass
class WorkOrder:
    objective: str
    worker_type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    dependencies: Tuple[str, ...] = field(default_factory=tuple)
    required_capabilities: Tuple[str, ...] = field(default_factory=tuple)
    expected_value: float = 1.0
    success_probability: float = 0.5
    evidence_strength: float = 0.5
    strategic_reuse: float = 0.5
    cost: float = 1.0
    risk: float = 0.0
    urgency: float = 0.0
    max_attempts: int = 2
    work_order_id: str = field(default_factory=lambda: f"wo_{uuid.uuid4().hex}")
    status: WorkStatus = WorkStatus.PENDING
    attempts: int = 0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def priority(self) -> float:
        denominator = max(0.001, self.cost + self.risk + 1.0)
        upside = (
            max(0.0, self.success_probability)
            * max(0.0, self.expected_value)
            * max(0.0, self.strategic_reuse)
            * max(0.0, self.evidence_strength)
        )
        return (upside / denominator) * (1.0 + max(0.0, self.urgency))


@dataclass(frozen=True)
class Receipt:
    work_order_id: str
    status: str
    result_hash: str
    created_at: float
    evidence_count: int
    receipt_hash: str


Worker = Callable[[WorkOrder, CapabilityLease], Awaitable[Dict[str, Any]]]
Verifier = Callable[[WorkOrder, Dict[str, Any]], Awaitable[Tuple[bool, str]]]


class SQLiteLedger:
    """Crash-safe canonical state with WAL and hash-chained receipts."""

    def __init__(self, path: Union[str, Path]):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=FULL")
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS work_orders (
                    id TEXT PRIMARY KEY,
                    body TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority REAL NOT NULL,
                    updated_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS receipts (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    work_order_id TEXT NOT NULL,
                    body TEXT NOT NULL,
                    receipt_hash TEXT NOT NULL UNIQUE,
                    created_at REAL NOT NULL
                );
                """
            )
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    @staticmethod
    def _encode(order: WorkOrder) -> str:
        body = asdict(order)
        body["status"] = order.status.value
        return json.dumps(body, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _decode(body: str) -> WorkOrder:
        raw = json.loads(body)
        raw["status"] = WorkStatus(raw["status"])
        raw["dependencies"] = tuple(raw.get("dependencies", ()))
        raw["required_capabilities"] = tuple(raw.get("required_capabilities", ()))
        return WorkOrder(**raw)

    def save(self, order: WorkOrder) -> None:
        order.updated_at = time.time()
        encoded = self._encode(order)
        with self._lock:
            self._conn.execute(
                """INSERT INTO work_orders(id, body, status, priority, updated_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET
                     body=excluded.body, status=excluded.status,
                     priority=excluded.priority, updated_at=excluded.updated_at""",
                (order.work_order_id, encoded, order.status.value, order.priority(), order.updated_at),
            )
            self._conn.commit()

    def get(self, work_order_id: str) -> Optional[WorkOrder]:
        with self._lock:
            row = self._conn.execute("SELECT body FROM work_orders WHERE id=?", (work_order_id,)).fetchone()
        return self._decode(row["body"]) if row else None

    def all(self) -> List[WorkOrder]:
        with self._lock:
            rows = self._conn.execute("SELECT body FROM work_orders ORDER BY updated_at, id").fetchall()
        return [self._decode(row["body"]) for row in rows]

    def recover_interrupted(self) -> int:
        """Return interrupted work to pending; attempts remain recorded."""
        recovered = 0
        for order in self.all():
            if order.status in (WorkStatus.RUNNING, WorkStatus.VERIFYING, WorkStatus.READY):
                order.status = WorkStatus.PENDING
                order.error = "recovered_after_interruption"
                self.save(order)
                recovered += 1
        return recovered

    def append_receipt(self, order: WorkOrder) -> Receipt:
        result = order.result or {}
        canonical_result = json.dumps(result, sort_keys=True, separators=(",", ":"), default=str)
        result_hash = hashlib.sha256(canonical_result.encode()).hexdigest()
        evidence = result.get("evidence", []) if isinstance(result, dict) else []
        created_at = time.time()
        with self._lock:
            row = self._conn.execute("SELECT receipt_hash FROM receipts ORDER BY seq DESC LIMIT 1").fetchone()
            previous = row["receipt_hash"] if row else "GENESIS"
            preimage = f"{previous}|{order.work_order_id}|{order.status.value}|{result_hash}|{created_at:.9f}"
            receipt_hash = hashlib.sha256(preimage.encode()).hexdigest()
            receipt = Receipt(
                work_order_id=order.work_order_id,
                status=order.status.value,
                result_hash=result_hash,
                created_at=created_at,
                evidence_count=len(evidence) if isinstance(evidence, list) else 0,
                receipt_hash=receipt_hash,
            )
            self._conn.execute(
                "INSERT INTO receipts(work_order_id, body, receipt_hash, created_at) VALUES (?, ?, ?, ?)",
                (order.work_order_id, json.dumps(asdict(receipt), sort_keys=True), receipt_hash, created_at),
            )
            self._conn.commit()
        return receipt

    def receipts(self) -> List[Receipt]:
        with self._lock:
            rows = self._conn.execute("SELECT body FROM receipts ORDER BY seq").fetchall()
        return [Receipt(**json.loads(row["body"])) for row in rows]


class ExecutionMesh:
    """DAG scheduler + parallel dispatcher + capability and verification gates."""

    def __init__(
        self,
        ledger: SQLiteLedger,
        verifier: Verifier,
        *,
        max_concurrency: int = 8,
    ):
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be >= 1")
        self.ledger = ledger
        self.verifier = verifier
        self.max_concurrency = max_concurrency
        self._workers: Dict[str, Worker] = {}
        self._leases: Dict[str, CapabilityLease] = {}

    def register_worker(self, worker_type: str, worker: Worker, lease: CapabilityLease) -> None:
        if lease.worker_type != worker_type:
            raise ValueError("lease worker_type must match registered worker_type")
        self._workers[worker_type] = worker
        self._leases[worker_type] = lease

    def submit(self, orders: Sequence[WorkOrder]) -> List[str]:
        if not orders:
            return []
        known = {o.work_order_id for o in self.ledger.all()} | {o.work_order_id for o in orders}
        if len({o.work_order_id for o in orders}) != len(orders):
            raise ValueError("duplicate work_order_id in submission")
        for order in orders:
            missing = set(order.dependencies) - known
            if missing:
                raise ValueError(f"unknown dependencies for {order.work_order_id}: {sorted(missing)}")
            if order.max_attempts < 1:
                raise ValueError("max_attempts must be >= 1")
        self._assert_acyclic(list(self.ledger.all()) + list(orders))
        for order in orders:
            self.ledger.save(order)
        return [o.work_order_id for o in orders]

    @staticmethod
    def _assert_acyclic(orders: Sequence[WorkOrder]) -> None:
        graph = {o.work_order_id: set(o.dependencies) for o in orders}
        visiting: Set[str] = set()
        visited: Set[str] = set()

        def visit(node: str) -> None:
            if node in visiting:
                raise ValueError(f"dependency cycle detected at {node}")
            if node in visited:
                return
            visiting.add(node)
            for dep in graph.get(node, set()):
                if dep in graph:
                    visit(dep)
            visiting.remove(node)
            visited.add(node)

        for node in graph:
            visit(node)

    def _refresh_states(self) -> None:
        orders = {o.work_order_id: o for o in self.ledger.all()}
        for order in orders.values():
            if order.status not in (WorkStatus.PENDING, WorkStatus.READY):
                continue
            deps = [orders[d] for d in order.dependencies if d in orders]
            if any(d.status in (WorkStatus.FAILED, WorkStatus.BLOCKED) for d in deps):
                order.status = WorkStatus.BLOCKED
                order.error = "dependency_failed"
                self.ledger.save(order)
            elif all(d.status == WorkStatus.COMPLETED for d in deps):
                order.status = WorkStatus.READY
                order.error = None
                self.ledger.save(order)

    async def _execute_one(self, work_order_id: str, semaphore: asyncio.Semaphore) -> None:
        async with semaphore:
            order = self.ledger.get(work_order_id)
            if order is None or order.status != WorkStatus.READY:
                return
            worker = self._workers.get(order.worker_type)
            lease = self._leases.get(order.worker_type)
            if worker is None or lease is None:
                order.status = WorkStatus.BLOCKED
                order.error = f"no_registered_worker:{order.worker_type}"
                self.ledger.save(order)
                return
            if not lease.permits(order.required_capabilities):
                order.status = WorkStatus.BLOCKED
                order.error = "capability_lease_denied_or_expired"
                self.ledger.save(order)
                return

            order.status = WorkStatus.RUNNING
            order.attempts += 1
            order.error = None
            self.ledger.save(order)
            try:
                result = await worker(order, lease)
                if not isinstance(result, dict):
                    raise TypeError("worker result must be a dict")
                order.result = result
                order.status = WorkStatus.VERIFYING
                self.ledger.save(order)
                accepted, reason = await self.verifier(order, result)
                if accepted:
                    order.status = WorkStatus.COMPLETED
                    order.error = None
                    self.ledger.save(order)
                    self.ledger.append_receipt(order)
                elif order.attempts < order.max_attempts:
                    order.status = WorkStatus.PENDING
                    order.error = f"verification_rejected:{reason}"
                    self.ledger.save(order)
                else:
                    order.status = WorkStatus.FAILED
                    order.error = f"verification_rejected:{reason}"
                    self.ledger.save(order)
            except Exception as exc:
                order.error = f"{type(exc).__name__}:{exc}"
                order.status = WorkStatus.PENDING if order.attempts < order.max_attempts else WorkStatus.FAILED
                self.ledger.save(order)

    async def run_until_idle(self) -> Dict[str, int]:
        """Execute runnable graph waves until no more work can progress."""
        self.ledger.recover_interrupted()
        semaphore = asyncio.Semaphore(self.max_concurrency)
        while True:
            self._refresh_states()
            ready = sorted(
                (o for o in self.ledger.all() if o.status == WorkStatus.READY),
                key=lambda o: (-o.priority(), o.created_at, o.work_order_id),
            )
            if not ready:
                pending = [o for o in self.ledger.all() if o.status == WorkStatus.PENDING]
                if pending:
                    self._refresh_states()
                    after_ready = [o for o in self.ledger.all() if o.status == WorkStatus.READY]
                    if after_ready:
                        continue
                break
            await asyncio.gather(*(self._execute_one(o.work_order_id, semaphore) for o in ready))

        counts: Dict[str, int] = {status.value: 0 for status in WorkStatus}
        for order in self.ledger.all():
            counts[order.status.value] += 1
        return counts

    def portfolio(self) -> List[Dict[str, Any]]:
        orders = sorted(self.ledger.all(), key=lambda o: (-o.priority(), o.created_at))
        return [
            {
                "work_order_id": o.work_order_id,
                "objective": o.objective,
                "worker_type": o.worker_type,
                "status": o.status.value,
                "priority": round(o.priority(), 6),
                "attempts": o.attempts,
                "error": o.error,
            }
            for o in orders
        ]


async def evidence_verifier(order: WorkOrder, result: Dict[str, Any]) -> Tuple[bool, str]:
    """Safe default: a claim must carry at least one structured evidence item."""
    evidence = result.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        return False, "missing_evidence"
    if any(not isinstance(item, Mapping) for item in evidence):
        return False, "malformed_evidence"
    return True, "verified"
