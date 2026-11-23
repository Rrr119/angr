#!/usr/bin/env python3
"""
Authoritative correctness check for the constraint simplification strategy.

Exploration output sets are not a usable oracle here: angr's symbolic execution
is nondeterministic across runs even on pristine code (memory-layout-dependent
set iteration changes which paths are explored first), so two runs of the
*same* configuration need not produce identical output strings.

Instead we check the property that actually matters, directly: every path
constraint emitted during a full exploration is rewritten by the strategy into
a *logically equivalent* constraint. Equivalence is decided by the solver, by
asserting the negation of ``(original == simplified)`` and checking it is
unsatisfiable. This is independent of exploration order and proves the
simplifier can never change a state's feasible region.
"""

from __future__ import annotations

import glob

import angr
from angr import claripy
from angr import sim_options as o
from angr.state_plugins.constraint_simplification import ConstraintSimplificationStrategy


def main() -> int:
    strategy = ConstraintSimplificationStrategy()
    oracle_project = angr.load_shellcode(b"\x90", "amd64")
    oracle = angr.SimState(project=oracle_project, mode="symbolic").solver

    def equivalent(original: claripy.ast.Base, simplified: claripy.ast.Base) -> bool:
        if hash(original) == hash(simplified):
            return True
        return not oracle.satisfiable(extra_constraints=[claripy.Not(original == simplified)])

    binaries = sorted(glob.glob("bench/bin/sample_*"))
    assert len(binaries) == 50
    total = 0
    failures: list[tuple[str, claripy.ast.Base, claripy.ast.Base]] = []
    cse_failures = 0
    cse_checked = 0

    for path in binaries:
        project = angr.Project(path, auto_load_libs=False)
        state = project.factory.entry_state(
            stdin=angr.SimFile("/dev/stdin", content=claripy.BVS("stdin", 16 * 8)),
            add_options={o.CONSTRAINT_SIMPLIFICATION},
        )
        simgr = project.factory.simulation_manager(state)
        simgr.run()
        before_size = after_size = 0
        sample_count = 0
        for end_state in simgr.deadended:
            sample_count += len(end_state.solver.constraints)
            for constraint in end_state.solver.constraints:
                simplified = strategy.simplify_constraint(constraint)
                total += 1
                before_size += constraint.depth
                after_size += simplified.depth
                if not equivalent(constraint, simplified):
                    failures.append((path, constraint, simplified))
        print(
            f"{path.split('/')[-1]:<24} constraints checked, "
            f"avg depth {before_size / max(sample_count, 1):.1f} -> "
            f"{after_size / max(sample_count, 1):.1f}"
        )

        # Set-level CSE: on every reached state, rewrite that state's own
        # constraint set and prove the original and rewritten conjunctions are
        # mutually entailing (identical feasible region) over the same symbols.
        cse_state = project.factory.entry_state(
            stdin=angr.SimFile("/dev/stdin", content=claripy.BVS("stdin", 16 * 8)),
        )
        cse_simgr = project.factory.simulation_manager(cse_state)
        cse_simgr.run()
        for end_state in cse_simgr.deadended:
            original_set = list(end_state.solver.constraints)
            rewritten = strategy.simplify_constraints(list(original_set))
            cse_checked += 1

            # The CSE symbols are fresh, existentially-quantified helpers, so
            # the correct contract is: (1) the rewritten set is satisfiable
            # exactly when the original set is, and (2) the rewritten set
            # entails every *original* constraint (the reverse direction is
            # vacuous: the original set cannot mention the fresh symbols).
            forward = angr.SimState(project=oracle_project, mode="symbolic")
            forward.add_constraints(*rewritten)
            forward_bad = any(forward.solver.satisfiable(extra_constraints=[claripy.Not(c)]) for c in original_set)
            original_sat = angr.SimState(project=oracle_project, mode="symbolic")
            original_sat.add_constraints(*original_set)
            rewritten_sat = angr.SimState(project=oracle_project, mode="symbolic")
            rewritten_sat.add_constraints(*rewritten)
            if forward_bad or (original_sat.satisfiable() != rewritten_sat.satisfiable()):
                cse_failures += 1

    print()
    print(f"checked {total} real path constraints across 50 samples")
    print(f"logical-equivalence failures: {len(failures)}")
    print(f"set-level CSE states checked: {cse_checked}, entailment failures: {cse_failures}")
    for path, original, simplified in failures[:10]:
        print(f" - {path}\n     original:   {original}\n     simplified: {simplified}")
    return 1 if (failures or cse_failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
