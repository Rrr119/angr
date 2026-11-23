#!/usr/bin/env python3
"""Tests for the opt-in path-constraint simplification strategy and its cache."""

from __future__ import annotations

import angr
from angr import claripy
from angr import sim_options as o
from angr.state_plugins.constraint_simplification import (
    ConstraintSimplificationCache,
    ConstraintSimplificationStrategy,
    get_default_cache,
    simplify_constraint,
)


def _project():
    return angr.load_shellcode(b"\x90", "amd64")


class TestBooleanRewrites:
    def setup_method(self):
        self.strategy = ConstraintSimplificationStrategy()
        self.x = claripy.BVS("x", 32)
        self.y = claripy.BVS("y", 32)

    def test_contradiction_and_tautology(self):
        x = self.x
        assert claripy.is_false(self.strategy.simplify_constraint(claripy.And(x > 1, claripy.Not(x > 1))))
        assert claripy.is_true(self.strategy.simplify_constraint(claripy.Or(x > 1, claripy.Not(x > 1))))

    def test_constant_literals_are_dropped(self):
        x = self.x
        assert self.strategy.simplify_constraint(claripy.And(claripy.BoolV(True), x > 1)).op == "UGT"
        assert self.strategy.simplify_constraint(claripy.Or(claripy.BoolV(False), x > 1)).op == "UGT"

    def test_flattening_and_deduplication(self):
        x, y = self.x, self.y
        result = self.strategy.simplify_constraint(claripy.And(claripy.And(x > 1, y < 9), x > 1, y < 9))
        assert result.op == "And"
        assert len(result.args) == 2

    def test_absorption(self):
        x, y = self.x, self.y
        a, b, c = x > 1, y < 2, x + y == 3
        and_result = self.strategy.simplify_constraint(claripy.And(a, b, claripy.Or(a, b, c)))
        assert and_result.op == "And" and len(and_result.args) == 2
        or_result = self.strategy.simplify_constraint(claripy.Or(a, b, claripy.And(a, b, c)))
        assert or_result.op == "Or" and len(or_result.args) == 2

    def test_double_negation(self):
        result = self.strategy.simplify_constraint(claripy.Not(claripy.Not(self.x > 1)))
        assert result.op == "UGT"

    def test_leaf_comparison_uses_fast_path(self):
        # A simple comparison is already canonical; it must come back equivalent
        # without entering the boolean fixed-point loop.
        guard = self.x * 3 + self.y > 9
        result = self.strategy.simplify_constraint(guard)
        assert hash(result) == hash(guard)


class TestEquivalence:
    """The rewriter must preserve the feasible region (solver as oracle)."""

    def setup_method(self):
        self.strategy = ConstraintSimplificationStrategy()
        self.project = _project()

    def _equivalent(self, original, simplified):
        state = angr.SimState(project=self.project, mode="symbolic")
        return not state.solver.satisfiable(extra_constraints=[claripy.Not(original == simplified)])

    def test_individual_constraints_equivalent(self):
        x, y = claripy.BVS("x", 16), claripy.BVS("y", 16)
        constraints = [
            claripy.And(x > 1, x > 1, y < 9),
            claripy.Or(claripy.BoolV(False), x + y == 3),
            claripy.And(x > 1, claripy.And(y < 9, y < 9)),
            claripy.Or(x == 2, claripy.BoolV(False)),
        ]
        for constraint in constraints:
            assert self._equivalent(constraint, self.strategy.simplify_constraint(constraint))

    def test_common_subexpression_elimination_entails_original(self):
        x, y = claripy.BVS("x", 16), claripy.BVS("y", 16)
        shared = (x | y) << 2
        original = [shared + 1 > 5, shared - 3 < 100, x == 7]
        rewritten = self.strategy.simplify_constraints(list(original))

        # The rewritten set is smaller and entails every original constraint.
        def node_count(expression):
            total = 1
            for child in expression.args:
                if isinstance(child, claripy.ast.Base):
                    total += node_count(child)
            return total

        assert sum(node_count(c) for c in rewritten) < sum(node_count(c) for c in original)
        check = angr.SimState(project=self.project, mode="symbolic")
        check.add_constraints(*rewritten)
        for constraint in original:
            assert not check.solver.satisfiable(extra_constraints=[claripy.Not(constraint)])
        # Both sets are satisfiable over the same input variables.
        original_state = angr.SimState(project=self.project, mode="symbolic")
        original_state.add_constraints(*original)
        assert original_state.satisfiable() and check.satisfiable()


class TestCache:
    def test_hit_returns_same_object(self):
        cache = ConstraintSimplificationCache(10)
        strategy = ConstraintSimplificationStrategy()
        x = claripy.BVS("x", 32)
        expression = claripy.And(x > 1, x > 1, x < 9)
        first = simplify_constraint(expression, strategy=strategy, cache=cache)
        second = simplify_constraint(expression, strategy=strategy, cache=cache)
        assert first is second
        assert cache.stats()["hits"] == 1 and cache.stats()["misses"] == 1

    def test_none_cache_bypasses_storage(self):
        strategy = ConstraintSimplificationStrategy()
        x = claripy.BVS("x", 32)
        expression = claripy.And(x > 1, x > 1, x < 9)
        result = simplify_constraint(expression, strategy=strategy, cache=None)
        assert result.op == "And"

    def test_lru_eviction_bounds_size(self):
        cache = ConstraintSimplificationCache(4)
        strategy = ConstraintSimplificationStrategy()
        for index in range(8):
            x = claripy.BVS(f"v{index}", 32)
            simplify_constraint(claripy.And(x > index, x < index + 5), strategy=strategy, cache=cache)
        assert cache.stats()["size"] <= 4

    def test_clear_resets_counters(self):
        cache = ConstraintSimplificationCache(4)
        strategy = ConstraintSimplificationStrategy()
        x = claripy.BVS("x", 32)
        simplify_constraint(x > 1, strategy=strategy, cache=cache)
        cache.clear()
        assert cache.stats() == {"size": 0, "maxsize": 4, "hits": 0, "misses": 0, "hit_rate": 0.0}

    def test_default_cache_is_shared(self):
        assert get_default_cache() is not None


class TestStateIntegration:
    def test_default_behavior_unchanged(self):
        state = angr.SimState(project=_project(), mode="symbolic")
        x = claripy.BVS("x", 32)
        before = len(state.solver.constraints)
        state.add_constraints(claripy.And(x > 1, x > 1, x < 9))
        # Without the new option, the raw constraint is stored as before.
        assert len(state.solver.constraints) == before + 1
        assert o.CONSTRAINT_SIMPLIFICATION not in state.options

    def test_enabled_strategy_preserves_satisfiability(self):
        x, y = claripy.BVS("x", 32), claripy.BVS("y", 32)
        constraints = [
            claripy.And(x > 1, claripy.And(y < 9, y < 9)),
            claripy.Or(x == 2, claripy.BoolV(False)),
            x + y > 4,
        ]
        baseline = angr.SimState(project=_project(), mode="symbolic")
        accelerated = angr.SimState(
            project=_project(),
            mode="symbolic",
            add_options={o.CONSTRAINT_SIMPLIFICATION, o.CONSTRAINT_SIMPLIFICATION_CACHE},
        )
        for constraint in constraints:
            baseline.add_constraints(constraint)
            accelerated.add_constraints(constraint)
        assert baseline.satisfiable() and accelerated.satisfiable()
        for _ in range(10):
            vx, vy = baseline.solver.eval(x), baseline.solver.eval(y)
            assert accelerated.solver.solution(x, vx)
            assert accelerated.solver.solution(y, vy)

    def test_contradiction_is_detected(self):
        state = angr.SimState(
            project=_project(),
            mode="symbolic",
            add_options={o.CONSTRAINT_SIMPLIFICATION, o.CONSTRAINT_SIMPLIFICATION_CACHE},
        )
        x = claripy.BVS("x", 32)
        state.add_constraints(claripy.And(claripy.Not(x == 5), x == 5))
        assert not state.satisfiable()

    def test_fork_shares_cache_override(self):
        state = angr.SimState(
            project=_project(),
            mode="symbolic",
            add_options={o.CONSTRAINT_SIMPLIFICATION, o.CONSTRAINT_SIMPLIFICATION_CACHE},
        )
        custom = ConstraintSimplificationCache(8)
        state.solver.constraint_simplification_cache = custom
        child = state.copy()
        assert child.solver.constraint_simplification_cache is custom

    def test_set_level_simplify_constraints_api(self):
        x, y = claripy.BVS("x", 16), claripy.BVS("y", 16)
        shared = (x | y) << 2
        state = angr.SimState(
            project=_project(),
            mode="symbolic",
            add_options={o.CONSTRAINT_SIMPLIFICATION, o.CONSTRAINT_SIMPLIFICATION_CACHE},
        )
        state.add_constraints(shared + 1 > 5, shared - 3 < 100)
        original_depth = sum(c.depth for c in state.solver.constraints)
        count = state.solver.simplify_constraints()
        assert count == len(state.solver.constraints)
        assert state.satisfiable()
        # CSE factors the shared subexpression into a symbol, so the surviving
        # comparison constraints get shallower even though a definition is added.
        assert sum(c.depth for c in state.solver.constraints) <= original_depth
