#!/usr/bin/env python3
"""
Benchmark path-constraint simplification on 50 generated binaries.

Two complementary measurements are reported.

1. End-to-end exploration. Every sample is symbolically explored under three
   configurations (``baseline``: stock angr; ``strategy``: simplification
   enabled, cache off; ``cached``: simplification plus the shared LRU cache).
   We record wall time plus the *size* of the accumulated path constraints
   (AST depth and node count), the direct output of the feature and independent
   of angr's nondeterministic exploration order.

2. Rewrite microbenchmark. The exact constraints captured from a baseline
   exploration are replayed through the uncached and cached strategy, so the
   cache hit rate and per-constraint rewrite cost are measured on real
   constraints rather than synthetic ones.

Correctness is established separately by ``verify_correctness.py``: angr's
exploration output is nondeterministic across runs even on pristine code, so it
cannot serve as an equivalence oracle; the solver-based proof in that script
does.

Usage::

    .venv/bin/python bench/bench_simplification.py
    .venv/bin/python bench/bench_simplification.py --runs 5 --json bench/results.json
"""

from __future__ import annotations

import argparse
import gc
import json
import statistics
import sys
import time
from pathlib import Path

import angr
from angr import claripy
from angr import sim_options as o
from angr.state_plugins import constraint_simplification as cs
from angr.state_plugins.constraint_simplification import ConstraintSimplificationStrategy

BENCH_DIR = Path(__file__).resolve().parent
BIN_DIR = BENCH_DIR / "bin"

CONFIGS = {
    "baseline": frozenset(),
    "strategy": frozenset({o.CONSTRAINT_SIMPLIFICATION}),
    "cached": frozenset({o.CONSTRAINT_SIMPLIFICATION, o.CONSTRAINT_SIMPLIFICATION_CACHE}),
}


def _ast_size(expr: claripy.ast.Base) -> int:
    """Number of AST nodes in an expression."""
    total = 1
    for child in expr.args:
        if isinstance(child, claripy.ast.Base):
            total += _ast_size(child)
    return total


def run_once(binary_path: Path, options: frozenset[str]) -> dict:
    project = angr.Project(str(binary_path), auto_load_libs=False)
    state = project.factory.entry_state(
        stdin=angr.SimFile("/dev/stdin", content=claripy.BVS("stdin", 16 * 8)),
        add_options=set(options),
    )
    simgr = project.factory.simulation_manager(state)

    start = time.perf_counter()
    simgr.run()
    elapsed = time.perf_counter() - start

    all_constraints = [constraint for end_state in simgr.deadended for constraint in end_state.solver.constraints]
    result = {
        "elapsed": elapsed,
        "deadended": len(simgr.deadended),
        "constraints": len(all_constraints),
        "constraint_depth": sum(c.depth for c in all_constraints),
        "constraint_nodes": sum(_ast_size(c) for c in all_constraints),
    }
    if o.CONSTRAINT_SIMPLIFICATION_CACHE in options:
        cache = cs.get_default_cache()
        result["cache"] = cache.stats() if cache is not None else None
    return result


def collect_constraints(binary_path: Path) -> list[claripy.ast.Base]:
    """Capture the raw path constraints a baseline exploration produces."""
    project = angr.Project(str(binary_path), auto_load_libs=False)
    state = project.factory.entry_state(
        stdin=angr.SimFile("/dev/stdin", content=claripy.BVS("stdin", 16 * 8)),
    )
    simgr = project.factory.simulation_manager(state)
    simgr.run()
    return [constraint for end_state in simgr.deadended for constraint in end_state.solver.constraints]


def replay_microbenchmark(constraints: list[claripy.ast.Base]) -> dict:
    """Replay captured constraints through uncached and cached strategies."""
    strategy = ConstraintSimplificationStrategy()
    cache = cs.ConstraintSimplificationCache(maxsize=4096)

    gc.collect()
    start = time.perf_counter()
    uncached_outputs = []
    for _ in range(10):
        uncached_outputs = [strategy.simplify_constraint(c) for c in constraints]
    uncached_elapsed = (time.perf_counter() - start) / 10

    # Cold pass populates the cache; timed separately so it does not mask the
    # steady-state hit cost.
    cache.get_or_simplify_many(constraints, strategy)
    gc.collect()
    start = time.perf_counter()
    cached_outputs = []
    for _ in range(10):
        cached_outputs = [cache.get_or_simplify(c, strategy) for c in constraints]
    cached_elapsed = (time.perf_counter() - start) / 10

    assert all(hash(a) == hash(b) for a, b in zip(uncached_outputs, cached_outputs, strict=True))

    raw_depth = sum(c.depth for c in constraints)
    raw_nodes = sum(_ast_size(c) for c in constraints)

    # Set-level common subexpression elimination over the whole constraint set.
    cse_outputs = strategy.simplify_constraints(list(uncached_outputs))
    simple_depth = sum(c.depth for c in uncached_outputs)
    simple_nodes = sum(_ast_size(c) for c in uncached_outputs)
    cse_depth = sum(c.depth for c in cse_outputs)
    cse_nodes = sum(_ast_size(c) for c in cse_outputs)

    # Time a representative solver query (satisfiability of the full set) before
    # and after CSE to capture the downstream benefit of the smaller set.
    oracle_project = angr.load_shellcode(b"\x90", "amd64")
    gc.collect()
    start = time.perf_counter()
    for _ in range(5):
        raw_state = angr.SimState(project=oracle_project, mode="symbolic")
        raw_state.add_constraints(*constraints)
        raw_state.solver.satisfiable()
    raw_query = (time.perf_counter() - start) / 5
    gc.collect()
    start = time.perf_counter()
    for _ in range(5):
        cse_state = angr.SimState(project=oracle_project, mode="symbolic")
        cse_state.add_constraints(*cse_outputs)
        cse_state.solver.satisfiable()
    cse_query = (time.perf_counter() - start) / 5

    return {
        "n_constraints": len(constraints),
        "uncached_rewrite_s": uncached_elapsed,
        "cached_rewrite_s": cached_elapsed,
        "rewrite_speedup": uncached_elapsed / max(cached_elapsed, 1e-12),
        "raw_depth": raw_depth,
        "simplified_depth": simple_depth,
        "depth_reduction": 1 - (simple_depth / max(raw_depth, 1)),
        "raw_nodes": raw_nodes,
        "simplified_nodes": simple_nodes,
        "node_reduction": 1 - (simple_nodes / max(raw_nodes, 1)),
        "cse_depth": cse_depth,
        "cse_nodes": cse_nodes,
        "cse_depth_reduction": 1 - (cse_depth / max(raw_depth, 1)),
        "cse_node_reduction": 1 - (cse_nodes / max(raw_nodes, 1)),
        "raw_query_s": raw_query,
        "cse_query_s": cse_query,
        "query_speedup": raw_query / max(cse_query, 1e-12),
        "cache": cache.stats(),
    }


def benchmark_sample(binary_path: Path, runs: int) -> dict:
    record: dict = {"sample": binary_path.name}
    for name, options in CONFIGS.items():
        timings = []
        last = None
        for _ in range(runs):
            if name == "cached":
                cache = cs.get_default_cache()
                if cache is not None:
                    cache.clear()
            gc.collect()
            last = run_once(binary_path, options)
            timings.append(last.pop("elapsed"))
        record[name] = {
            **last,
            "elapsed_mean": statistics.mean(timings),
            "elapsed_median": statistics.median(timings),
            "elapsed_min": min(timings),
        }
    record["micro"] = replay_microbenchmark(collect_constraints(binary_path))
    return record


def summarize(records: list[dict]) -> dict:
    base = sum(r["baseline"]["elapsed_median"] for r in records)
    strat = sum(r["strategy"]["elapsed_median"] for r in records)
    cached = sum(r["cached"]["elapsed_median"] for r in records)
    micro = [r["micro"] for r in records]
    cached_speedups = [r["baseline"]["elapsed_median"] / max(r["cached"]["elapsed_median"], 1e-12) for r in records]
    cache_totals = {"hits": 0, "misses": 0}
    for entry in micro:
        stats = entry["cache"]
        cache_totals["hits"] += stats["hits"]
        cache_totals["misses"] += stats["misses"]
    total_lookups = cache_totals["hits"] + cache_totals["misses"]
    raw_nodes = sum(m["raw_nodes"] for m in micro)
    simple_nodes = sum(m["simplified_nodes"] for m in micro)
    raw_depth = sum(m["raw_depth"] for m in micro)
    simple_depth = sum(m["simplified_depth"] for m in micro)
    cse_nodes = sum(m["cse_nodes"] for m in micro)
    cse_depth = sum(m["cse_depth"] for m in micro)
    return {
        "samples": len(records),
        "total_baseline_s": base,
        "total_strategy_s": strat,
        "total_cached_s": cached,
        "strategy_speedup": base / strat if strat else None,
        "cached_speedup": base / cached if cached else None,
        "cached_vs_strategy_speedup": strat / cached if cached else None,
        "per_sample_cached_speedup_median": statistics.median(cached_speedups),
        "per_sample_cached_speedup_min": min(cached_speedups),
        "per_sample_cached_speedup_max": max(cached_speedups),
        "per_sample_cached_wins": sum(1 for value in cached_speedups if value > 1.0),
        "raw_constraint_nodes": raw_nodes,
        "simplified_constraint_nodes": simple_nodes,
        "node_reduction": 1 - simple_nodes / max(raw_nodes, 1),
        "raw_constraint_depth": raw_depth,
        "simplified_constraint_depth": simple_depth,
        "depth_reduction": 1 - simple_depth / max(raw_depth, 1),
        "cse_constraint_nodes": cse_nodes,
        "cse_constraint_depth": cse_depth,
        "cse_node_reduction": 1 - cse_nodes / max(raw_nodes, 1),
        "cse_depth_reduction": 1 - cse_depth / max(raw_depth, 1),
        "total_uncached_rewrite_s": sum(m["uncached_rewrite_s"] for m in micro),
        "total_cached_rewrite_s": sum(m["cached_rewrite_s"] for m in micro),
        "total_raw_query_s": sum(m["raw_query_s"] for m in micro),
        "total_cse_query_s": sum(m["cse_query_s"] for m in micro),
        "query_speedup_median": statistics.median(m["query_speedup"] for m in micro),
        "cache_hits": cache_totals["hits"],
        "cache_misses": cache_totals["misses"],
        "cache_hit_rate": (cache_totals["hits"] / total_lookups) if total_lookups else 0.0,
    }


def print_table(records: list[dict], summary: dict) -> None:
    header = (
        f"{'sample':<24}{'baseline':>10}{'strategy':>10}{'cached':>10}"
        f"{'CSE cut':>9}{'query':>8}{'rewrite':>9}{'hit%':>7}"
    )
    print(header)
    print("-" * len(header))
    for r in records:
        b = r["baseline"]["elapsed_median"]
        s = r["strategy"]["elapsed_median"]
        c = r["cached"]["elapsed_median"]
        micro = r["micro"]
        hit_rate = micro["cache"]["hit_rate"] * 100
        print(
            f"{r['sample']:<24}{b:>9.3f}s{s:>9.3f}s{c:>9.3f}s"
            f"{micro['cse_node_reduction'] * 100:>8.1f}%{micro['query_speedup']:>7.2f}x"
            f"{micro['rewrite_speedup']:>8.2f}x{hit_rate:>6.1f}%"
        )
    print("-" * len(header))
    print(
        f"{'TOTAL':<24}{summary['total_baseline_s']:>9.3f}s"
        f"{summary['total_strategy_s']:>9.3f}s{summary['total_cached_s']:>9.3f}s"
    )
    print()
    print(f"end-to-end strategy-only speedup   : {summary['strategy_speedup']:.2f}x")
    print(f"end-to-end strategy+cache speedup   : {summary['cached_speedup']:.2f}x")
    print(f"cache adds over strategy-only       : {summary['cached_vs_strategy_speedup']:.2f}x")
    print(
        f"per-sample cached speedup           : median {summary['per_sample_cached_speedup_median']:.2f}x "
        f"(min {summary['per_sample_cached_speedup_min']:.2f}x, max "
        f"{summary['per_sample_cached_speedup_max']:.2f}x), {summary['per_sample_cached_wins']}/50 faster"
    )
    print(
        f"constraint node reduction           : "
        f"{summary['raw_constraint_nodes']} -> {summary['simplified_constraint_nodes']} "
        f"({summary['node_reduction'] * 100:.1f}% smaller)"
    )
    print(
        f"after set-level CSE                 : "
        f"{summary['raw_constraint_nodes']} -> {summary['cse_constraint_nodes']} "
        f"({summary['cse_node_reduction'] * 100:.1f}% smaller)"
    )
    print(
        f"constraint depth reduction          : "
        f"{summary['raw_constraint_depth']} -> {summary['simplified_constraint_depth']} "
        f"({summary['depth_reduction'] * 100:.1f}% smaller)"
    )
    print(
        f"depth after set-level CSE           : "
        f"{summary['raw_constraint_depth']} -> {summary['cse_constraint_depth']} "
        f"({summary['cse_depth_reduction'] * 100:.1f}% smaller)"
    )
    print(f"replay rewrite time (uncached)      : {summary['total_uncached_rewrite_s']:.4f}s")
    print(f"replay rewrite time (cached)        : {summary['total_cached_rewrite_s']:.4f}s")
    print(
        f"solver query time raw vs CSE        : {summary['total_raw_query_s']:.4f}s vs "
        f"{summary['total_cse_query_s']:.4f}s (median {summary['query_speedup_median']:.2f}x)"
    )
    print(
        f"cache lookups                       : {summary['cache_hits']} hits / "
        f"{summary['cache_misses']} misses ({summary['cache_hit_rate'] * 100:.1f}% hit rate)"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=3, help="timing repetitions per configuration")
    parser.add_argument("--json", type=Path, default=None, help="optional path to write full results")
    args = parser.parse_args()

    binaries = sorted(BIN_DIR.glob("sample_*"))
    if len(binaries) != 50:
        print(f"expected 50 samples in {BIN_DIR}, found {len(binaries)}", file=sys.stderr)
        return 2

    # Warm up project loading and the JIT/Rust paths so the first samples do not
    # pay one-off initialization cost that would dominate their short runtimes.
    for binary in binaries[:3]:
        for options in CONFIGS.values():
            run_once(binary, options)

    records = []
    for index, binary in enumerate(binaries, start=1):
        record = benchmark_sample(binary, args.runs)
        records.append(record)
        print(
            f"[{index:2d}/50] {binary.name} done "
            f"(baseline {record['baseline']['elapsed_median']:.3f}s, "
            f"cached {record['cached']['elapsed_median']:.3f}s, "
            f"node cut {record['micro']['node_reduction'] * 100:.0f}%)",
            flush=True,
        )

    summary = summarize(records)
    print()
    print_table(records, summary)
    print("\ncorrectness: see verify_correctness.py for solver-proven logical equivalence")

    if args.json is not None:
        args.json.write_text(json.dumps({"summary": summary, "records": records}, indent=2))
        print(f"\nfull results written to {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
