# Path-constraint simplification benchmark

This directory benchmarks the opt-in constraint simplification added in
`angr/state_plugins/constraint_simplification.py`. It is self-contained: the 50
target binaries are generated from C templates, so no external `angr/binaries`
checkout is required.

## Layout

- `gen_samples.py` - deterministically generates 50 C programs (branch-, loop-,
  switch- and mixed-heavy) into `src/` and compiles them into `bin/`.
- `bench_simplification.py` - the timing and constraint-size comparison across
  three configurations.
- `verify_correctness.py` - solver-proven logical-equivalence checks.
- `results.json` - machine-readable output of the latest full run.

## Reproducing

```bash
.venv/bin/python bench/gen_samples.py
PYTHONHASHSEED=0 .venv/bin/python bench/verify_correctness.py
PYTHONHASHSEED=0 .venv/bin/python bench/bench_simplification.py --runs 3 --json bench/results.json
```

`PYTHONHASHSEED=0` is only needed for reproducibility of angr's internal
iteration order; it does not affect the equivalence proof.

## What is measured

Three configurations are compared:

- `baseline` - stock angr options.
- `strategy` - `CONSTRAINT_SIMPLIFICATION` enabled, cache disabled.
- `cached` - `CONSTRAINT_SIMPLIFICATION` plus the shared LRU cache
  (`CONSTRAINT_SIMPLIFICATION_CACHE`).

Reported metrics:

- End-to-end symbolic-execution wall time per sample (median of `--runs`).
- Constraint AST node/depth counts, before and after set-level common
  subexpression elimination (CSE), which is exposed through
  `state.solver.simplify_constraints()`.
- Rewrite microbenchmark: the captured real constraints are replayed through
  the uncached and warm-cached strategy.
- A satisfiability query on the raw versus CSE-reduced constraint sets.
- Cache hit/miss counters.

## How to read the numbers

- The per-constraint boolean pipeline is deliberately cheap: leaf comparisons
  take a fast path, so end-to-end exploration time is roughly neutral to
  slightly faster, while the cache removes redundant rewrites across forked
  states (the warm-cache rewrite path is consistently faster, with a ~97% hit
  rate on the generated corpus).
- Set-level CSE is where the structural win lives: it roughly halves the
  constraint AST size (about 53% fewer nodes, 51% less depth on this corpus),
  which reduces Python-side AST handling and memory. It does not always reduce
  a single z3 `check-sat` because z3 already performs aggressive preprocessing;
  its benefit grows for workloads that repeatedly inspect or transmit the same
  deep constraint sets.

## Why output strings are not used as the correctness oracle

angr's symbolic execution is nondeterministic across runs even on pristine
code: memory-layout-dependent set iteration changes the order in which paths
are explored, so two runs of the *same* configuration can print different
output strings. `verify_correctness.py` therefore proves the property that
actually matters directly - every rewritten constraint is logically equivalent
  to its input, decided by the solver (the negation of `original == simplified`
  must be unsatisfiable), and CSE sets are checked for mutual entailment and
  equal satisfiability.
