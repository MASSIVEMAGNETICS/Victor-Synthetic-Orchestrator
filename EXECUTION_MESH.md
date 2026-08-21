# Victor Execution Mesh v0.1

The Execution Mesh turns Victor from a sequential agent coordinator into a durable portfolio execution runtime.

## Contract

Every unit of work is a `WorkOrder`. A WorkOrder declares:

- objective and worker type
- explicit dependencies
- required capabilities
- bounded retry count
- economic priority inputs
- durable status/result/error state

Workers receive a `CapabilityLease`. The mesh fails closed when a WorkOrder requests capabilities not present in that lease or when the lease has expired.

Worker results do not become completed work merely because a worker returned successfully. Results pass through an independent verifier. The default verifier requires structured evidence. Only verified completions generate hash-chained receipts.

## Lifecycle

```text
PENDING -> READY -> RUNNING -> VERIFYING -> COMPLETED
                      |             |
                      |             +-> PENDING (bounded retry)
                      +----------------> PENDING (bounded retry)

Any unrecoverable execution/verification failure -> FAILED
Missing worker, denied lease, or failed dependency -> BLOCKED
```

On restart, `RUNNING`, `VERIFYING`, and `READY` WorkOrders are recovered to `PENDING` and replayed with their attempt count preserved.

## Parallel DAG execution

Dependencies form a directed acyclic graph. The mesh rejects cycles at submission time. All currently runnable WorkOrders are dispatched concurrently, bounded by `max_concurrency`. Downstream work becomes runnable only after all dependencies are verified `COMPLETED`.

## Portfolio priority

The current deterministic score is:

```text
priority = (
    success_probability
    * expected_value
    * strategic_reuse
    * evidence_strength
) / (cost + risk + 1)
* (1 + urgency)
```

This is deliberately simple and auditable. It can later be replaced or augmented with observed conversion/revenue data, a Bayesian estimator, or a multi-armed-bandit allocator without changing the WorkOrder execution contract.

## Receipts

Successful results are canonicalized and SHA-256 hashed. Each receipt includes the previous receipt hash in its preimage, producing an append-only hash chain suitable for later Chronos integration.

## Offline demo

From the repository root:

```bash
python -m examples.portfolio_demo
```

The demo dispatches six bounded workers concurrently:

1. Truth Compiler sales opportunities
2. music sync opportunities
3. B Heard growth opportunities
4. Massive Magnetics partnerships
5. website conversion opportunities
6. catalog monetization opportunities

The demo performs no network writes or external side effects. It proves scheduling, concurrency, leases, verification, persistence, receipts, and portfolio ranking.

## Tests

```bash
python -m pytest -q tests/test_execution_mesh.py
```

The v0.1 suite verifies:

- concurrent execution
- dependency ordering
- fail-closed capability leases
- verifier rejection without evidence
- crash recovery/replay
- priority scheduling

GitHub Actions independently runs the suite on Python 3.8 and 3.11 and runs the six-worker offline demo.

## Next production adapters

The runtime intentionally separates orchestration from external authority. Production adapters should be added behind narrow leases, for example:

- `research.read`
- `github.read`
- `github.branch`
- `github.commit`
- `email.draft`
- `email.send` (human-authorized or policy-authorized only)
- `catalog.read`
- `crm.write`
- `site.verify`

The next milestone is to replace the demo workers with real read-only opportunity scouts first, then add gated write capabilities only after their receipts and verification paths are stable.
