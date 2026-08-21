import asyncio
import time

from orchestrator.mesh import CapabilityLease, ExecutionMesh, SQLiteLedger, WorkOrder, WorkStatus, evidence_verifier


def run(coro):
    return asyncio.run(coro)


def worker(delay=0.0, with_evidence=True, tracker=None):
    async def _worker(order, lease):
        if tracker is not None:
            tracker.append(("start", order.work_order_id, time.monotonic()))
        await asyncio.sleep(delay)
        if tracker is not None:
            tracker.append(("end", order.work_order_id, time.monotonic()))
        result = {"ok": True}
        if with_evidence:
            result["evidence"] = [{"kind": "test", "source": "memory://test"}]
        return result
    return _worker


def make_mesh(tmp_path, max_concurrency=4):
    ledger = SQLiteLedger(tmp_path / "mesh.db")
    return ledger, ExecutionMesh(ledger, evidence_verifier, max_concurrency=max_concurrency)


def test_parallel_execution(tmp_path):
    ledger, mesh = make_mesh(tmp_path, 3)
    mesh.register_worker("x", worker(delay=0.12), CapabilityLease("x", ("read",)))
    mesh.submit([WorkOrder(f"job {i}", "x", required_capabilities=("read",)) for i in range(3)])
    started = time.monotonic()
    counts = run(mesh.run_until_idle())
    elapsed = time.monotonic() - started
    assert counts["completed"] == 3
    assert elapsed < 0.30, f"expected parallel execution, got {elapsed:.3f}s"
    assert len(ledger.receipts()) == 3
    ledger.close()


def test_dependency_dag(tmp_path):
    ledger, mesh = make_mesh(tmp_path)
    events = []
    mesh.register_worker("x", worker(tracker=events), CapabilityLease("x", ("read",)))
    first = WorkOrder("first", "x", required_capabilities=("read",))
    second = WorkOrder("second", "x", dependencies=(first.work_order_id,), required_capabilities=("read",))
    mesh.submit([first, second])
    run(mesh.run_until_idle())
    starts = [e[1] for e in events if e[0] == "start"]
    assert starts == [first.work_order_id, second.work_order_id]
    assert ledger.get(second.work_order_id).status == WorkStatus.COMPLETED
    ledger.close()


def test_capability_lease_fail_closed(tmp_path):
    ledger, mesh = make_mesh(tmp_path)
    mesh.register_worker("x", worker(), CapabilityLease("x", ("read",)))
    order = WorkOrder("danger", "x", required_capabilities=("send.email",))
    mesh.submit([order])
    run(mesh.run_until_idle())
    stored = ledger.get(order.work_order_id)
    assert stored.status == WorkStatus.BLOCKED
    assert "capability_lease" in stored.error
    ledger.close()


def test_verifier_rejects_claim_without_evidence(tmp_path):
    ledger, mesh = make_mesh(tmp_path)
    mesh.register_worker("x", worker(with_evidence=False), CapabilityLease("x", ()))
    order = WorkOrder("unverified", "x", max_attempts=1)
    mesh.submit([order])
    run(mesh.run_until_idle())
    stored = ledger.get(order.work_order_id)
    assert stored.status == WorkStatus.FAILED
    assert stored.error == "verification_rejected:missing_evidence"
    assert ledger.receipts() == []
    ledger.close()


def test_recovery_replays_interrupted_work(tmp_path):
    ledger, mesh = make_mesh(tmp_path)
    mesh.register_worker("x", worker(), CapabilityLease("x", ()))
    order = WorkOrder("recover me", "x")
    order.status = WorkStatus.RUNNING
    ledger.save(order)
    assert ledger.recover_interrupted() == 1
    assert ledger.get(order.work_order_id).status == WorkStatus.PENDING
    run(mesh.run_until_idle())
    assert ledger.get(order.work_order_id).status == WorkStatus.COMPLETED
    ledger.close()


def test_priority_orders_higher_expected_value_first(tmp_path):
    ledger, mesh = make_mesh(tmp_path, 1)
    events = []
    mesh.register_worker("x", worker(tracker=events), CapabilityLease("x", ()))
    low = WorkOrder("low", "x", expected_value=1, success_probability=0.5, evidence_strength=1, strategic_reuse=1)
    high = WorkOrder("high", "x", expected_value=10, success_probability=0.5, evidence_strength=1, strategic_reuse=1)
    mesh.submit([low, high])
    run(mesh.run_until_idle())
    starts = [e[1] for e in events if e[0] == "start"]
    assert starts[0] == high.work_order_id
    assert mesh.portfolio()[0]["work_order_id"] == high.work_order_id
    ledger.close()
