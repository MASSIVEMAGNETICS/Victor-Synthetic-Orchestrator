"""Offline demonstration of six portfolio workers executing concurrently."""
import asyncio
import json
import tempfile
from pathlib import Path

from orchestrator.mesh import CapabilityLease, ExecutionMesh, SQLiteLedger, WorkOrder, evidence_verifier


async def portfolio_worker(order: WorkOrder, lease: CapabilityLease):
    await asyncio.sleep(float(order.payload.get("delay", 0.05)))
    return {
        "summary": f"completed bounded scan for {order.objective}",
        "worker": order.worker_type,
        "lease_id": lease.lease_id,
        "evidence": [
            {
                "kind": "demo_receipt",
                "source": f"offline://{order.worker_type}/{order.work_order_id}",
                "claim": "worker completed its bounded execution contract",
            }
        ],
    }


async def main():
    db = Path(tempfile.gettempdir()) / "victor_execution_mesh_demo.db"
    if db.exists():
        db.unlink()
    ledger = SQLiteLedger(db)
    mesh = ExecutionMesh(ledger, evidence_verifier, max_concurrency=6)

    worker_types = [
        "truth_compiler_sales",
        "music_sync",
        "b_heard_growth",
        "mm_partnerships",
        "website_conversion",
        "catalog_monetization",
    ]
    for worker_type in worker_types:
        mesh.register_worker(
            worker_type,
            portfolio_worker,
            CapabilityLease(worker_type=worker_type, allowed=("research.read", "artifacts.write")),
        )

    orders = [
        WorkOrder(
            objective=objective,
            worker_type=worker_type,
            payload={"delay": 0.05},
            required_capabilities=("research.read",),
            expected_value=value,
            success_probability=prob,
            evidence_strength=0.8,
            strategic_reuse=0.8,
            cost=1.0,
        )
        for objective, worker_type, value, prob in [
            ("Find Truth Compiler customer opportunities", "truth_compiler_sales", 10, 0.20),
            ("Find music synchronization opportunities", "music_sync", 8, 0.15),
            ("Find B Heard creator acquisition opportunities", "b_heard_growth", 5, 0.25),
            ("Find Massive Magnetics partnership opportunities", "mm_partnerships", 9, 0.10),
            ("Audit website conversion opportunities", "website_conversion", 6, 0.30),
            ("Find catalog monetization opportunities", "catalog_monetization", 7, 0.20),
        ]
    ]
    mesh.submit(orders)
    counts = await mesh.run_until_idle()
    print(json.dumps({"counts": counts, "portfolio": mesh.portfolio(), "receipts": len(ledger.receipts())}, indent=2))
    ledger.close()


if __name__ == "__main__":
    asyncio.run(main())
