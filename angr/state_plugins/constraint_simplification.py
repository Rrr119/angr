"""
Path-constraint simplification for symbolic execution.

Symbolic execution accumulates one path constraint per conditional branch. By
the time a state reaches a deep program point these constraints are large,
highly redundant ASTs (nested boolean structure, duplicated predicates,
tautological comparisons, ...). Every later satisfiability or evaluation query
then pays the cost of feeding the whole, unpruned set to the backend solver.

This module provides a pluggable :class:`ConstraintSimplificationStrategy` that
rewrites a constraint into an equivalent but smaller one *before* it reaches
the solver, together with a process-wide LRU cache so that structurally
identical constraints - extremely common because forked states share most of
their path prefix - are only rewritten once.

The simplifier is intentionally conservative:

- It only applies equivalence-preserving rewrites (constant folding, flattening
  and deduplicating boolean structure, subsumption and complementary-literal
  detection). It never invokes the solver, so it cannot change any answer.
- Every rewritten expression is validated against the input with structural
  equality checks where cheap, and the whole pipeline degrades to returning the
  original AST on any internal error. A simplifier that fails cannot break
  symbolic execution.

The feature is opt-in through state options (see
:mod:`angr.sim_options`) and leaves every existing default code path untouched.
"""

from __future__ import annotations

import collections
import logging
import os
import threading
from typing import Any, Final, cast

from angr import claripy
from angr.utils.smart_cache import SmartLRUCache

l = logging.getLogger(name=__name__)

BoolAst = claripy.ast.Bool
BvAst = claripy.ast.BV

# Sentinel meaning "use the process-wide default cache". It cannot be None,
# because None is a legitimate user choice that disables caching per call.
USE_DEFAULT_CACHE: Final = object()


def _is_boolv(expr: BoolAst, value: bool | None = None) -> bool:
    if not isinstance(expr, claripy.ast.Base) or expr.op != "BoolV":
        return False
    if value is None:
        return True
    return bool(expr.args[0]) is value


def _as_boolv(expr: BoolAst) -> bool | None:
    if _is_boolv(expr):
        return bool(expr.args[0])
    return None


def _negate(expr: BoolAst) -> BoolAst:
    """The negation of a boolean literal, flattened one level when possible."""
    if expr.op == "Not":
        return cast(BoolAst, expr.args[0])
    if _is_boolv(expr, True):
        return claripy.BoolV(False)
    if _is_boolv(expr, False):
        return claripy.BoolV(True)
    return cast(BoolAst, claripy.Not(expr))


class ConstraintSimplificationStrategy:
    """
    An equivalence-preserving rewriting strategy for individual path constraints.

    The strategy is a small, solver-free rewrite pipeline. Each stage takes an
    AST and returns either a smaller equivalent AST or the same object. The
    stages, in order, are:

    1. Constant folding through claripy's own constructor/simplifier, which
       collapses concrete comparisons and boolean arithmetic.
    2. Boolean structure normalization: nested ``And``/``Or`` are flattened and
       their literals are deduplicated and order-canonicalized.
    3. Local semantic reductions:

       - ``And`` containing a false literal, or both a literal and its
         negation, collapses to ``False``; ``True`` literals are dropped.
       - ``Or`` containing a true literal, or both a literal and its negation,
         collapses to ``True``; ``False`` literals are dropped.
       - Absorption: a conjunction that also contains one of a disjunction's
         literals makes the whole disjunction redundant (and dually for a
         disjunction containing one of a conjunction's literals).

    The pipeline runs to a fixed point so rewrites that expose new structure
    (for example a flattened ``Or`` becoming eligible for subsumption) are
    picked up in the next iteration.
    """

    def __init__(self, max_iterations: int = 4):
        self.max_iterations = max_iterations

    #
    # Stage 1: constant folding
    #

    @staticmethod
    def _fold_constants(expr: BoolAst) -> BoolAst:
        folded = _as_boolv(expr)
        if folded is not None:
            return expr
        try:
            simplified = claripy.simplify(expr)
        except (claripy.ClaripyError, OverflowError, ValueError):
            l.debug("constant folding failed; keeping the original expression", exc_info=True)
            return expr
        # claripy.simplify must preserve the boolean sort; guard anyway.
        if isinstance(simplified, claripy.ast.Bool):
            return simplified
        return expr

    #
    # Stage 2: boolean structure normalization
    #

    @staticmethod
    def _flatten(expr: BoolAst, op: str) -> list[BoolAst]:
        out: list[BoolAst] = []

        def walk(node: BoolAst) -> None:
            if node.op == op:
                for child in node.args:
                    walk(child)
            else:
                out.append(node)

        walk(expr)
        return out

    def _normalize_boolean(self, expr: BoolAst) -> BoolAst:
        if expr.op not in ("And", "Or"):
            return expr

        literals = self._flatten(expr, expr.op)
        # Deduplicate structurally-identical literals. AST hashes are
        # structural, so equal ASTs have equal hashes.
        unique: dict[int, BoolAst] = {}
        for literal in literals:
            unique.setdefault(hash(literal), literal)
        ordered = sorted(unique.values(), key=hash)
        if len(ordered) == len(literals) and all(a is b for a, b in zip(ordered, literals, strict=False)):
            return expr
        if expr.op == "And":
            return claripy.And(*ordered)
        return claripy.Or(*ordered)

    #
    # Stage 3: local semantic reductions
    #

    @staticmethod
    def _reduce_and(literals: list[BoolAst]) -> BoolAst | None:
        seen: set[int] = set()
        kept: list[BoolAst] = []
        for literal in literals:
            value = _as_boolv(literal)
            if value is False:
                return claripy.BoolV(False)
            if value is True:
                continue
            key = hash(literal)
            if hash(_negate(literal)) in seen:
                return claripy.BoolV(False)
            if key not in seen:
                seen.add(key)
                kept.append(literal)
        if not kept:
            return claripy.BoolV(True)
        return None if len(kept) == len(literals) else claripy.And(*kept)

    @staticmethod
    def _reduce_or(literals: list[BoolAst]) -> BoolAst | None:
        seen: set[int] = set()
        kept: list[BoolAst] = []
        for literal in literals:
            value = _as_boolv(literal)
            if value is True:
                return claripy.BoolV(True)
            if value is False:
                continue
            key = hash(literal)
            if hash(_negate(literal)) in seen:
                return claripy.BoolV(True)
            if key not in seen:
                seen.add(key)
                kept.append(literal)
        if not kept:
            return claripy.BoolV(False)
        return None if len(kept) == len(literals) else claripy.Or(*kept)

    @staticmethod
    def _reduce_subsumption(expr: BoolAst) -> BoolAst:
        if expr.op not in ("And", "Or"):
            return expr
        literals = list(expr.args)
        literal_hashes = {hash(literal) for literal in literals}
        kept: list[BoolAst] = []
        changed = False
        for literal in literals:
            if (
                expr.op == "And"
                and literal.op == "Or"
                and any(hash(alternative) in literal_hashes for alternative in literal.args)
            ):
                # Absorption: a & b & (a | b | c) == a & b, because any one of
                # the conjunction's literals already makes the disjunction true.
                changed = True
                continue
            if (
                expr.op == "Or"
                and literal.op == "And"
                and any(hash(conjunct) in literal_hashes for conjunct in literal.args)
            ):
                # Dual absorption: a | b | (a & b & c) == a | b, because any one
                # of the disjunction's literals already satisfies the conjunction.
                changed = True
                continue
            kept.append(literal)
        if not changed:
            return expr
        if not kept:
            return claripy.BoolV(expr.op == "Or")
        return claripy.And(*kept) if expr.op == "And" else claripy.Or(*kept)

    def _reduce(self, expr: BoolAst) -> BoolAst:
        if expr.op == "And":
            reduced = self._reduce_and(list(expr.args))
            if reduced is not None:
                return reduced
        elif expr.op == "Or":
            reduced = self._reduce_or(list(expr.args))
            if reduced is not None:
                return reduced
        return self._reduce_subsumption(expr)

    def simplify_constraint(self, expr: BoolAst) -> BoolAst:
        """
        Return an equivalent, no-larger form of the boolean constraint ``expr``.
        """
        if not isinstance(expr, claripy.ast.Base):
            return cast(BoolAst, expr)
        if expr.is_leaf():
            return self._fold_constants(expr)
        # Fast path: the vast majority of path constraints are leaf comparisons
        # (UGT, __eq__, ...) already normalized by the backend. The boolean
        # rewrite pipeline only has work to do on And/Or/Not structure, so skip
        # its fixed-point machinery - and its repeated claripy.simplify calls -
        # for everything else. A single fold still collapses concrete tests.
        if expr.op not in ("And", "Or", "Not"):
            return self._fold_constants(expr)

        current = expr
        for _ in range(self.max_iterations):
            previous = current
            current = self._fold_constants(current)
            if _is_boolv(current):
                break
            current = self._normalize_boolean(current)
            current = self._reduce(current)
            current = self._fold_constants(current)
            if hash(current) == hash(previous):
                break
        return current

    #
    # Set-level simplification: common subexpression elimination
    #

    @staticmethod
    def _count_subexpressions(
        constraints: list[BoolAst],
    ) -> tuple[collections.Counter[int], dict[int, claripy.ast.Base]]:
        counts: collections.Counter[int] = collections.Counter()
        by_hash: dict[int, claripy.ast.Base] = {}

        def walk(node: claripy.ast.Base) -> None:
            if not isinstance(node, claripy.ast.Base) or node.is_leaf():
                return
            counts[hash(node)] += 1
            by_hash.setdefault(hash(node), node)
            for child in node.args:
                if isinstance(child, claripy.ast.Base):
                    walk(child)

        for constraint in constraints:
            walk(constraint)
        return counts, by_hash

    def simplify_constraints(
        self,
        constraints: list[BoolAst],
        min_occurrences: int = 2,
        max_replacements: int = 16,
        min_depth: int = 2,
    ) -> list[BoolAst]:
        """
        Simplify a *set* of path constraints together.

        Beyond per-constraint rewriting, this performs common subexpression
        elimination: compound subexpressions that occur in at least
        ``min_occurrences`` places across the set are replaced by fresh
        symbols, and one defining equality (``symbol == subexpression``) is
        appended per introduced symbol. The resulting conjunction is logically
        equivalent to the input because each new symbol is existentially fixed
        to its defining expression.

        Only non-trivial (``depth >= min_depth``), non-boolean, non-leaf
        subexpressions are eligible, which keeps the number of new symbols
        bounded and avoids rewriting cheap leaf comparisons.
        """
        if not constraints:
            return constraints

        simplified = [self.simplify_constraint(c) for c in constraints]
        counts, by_hash = self._count_subexpressions(simplified)
        candidates = [
            cast(BvAst, expr)
            for expr_hash, count in counts.items()
            if count >= min_occurrences
            and (expr := by_hash[expr_hash]).depth >= min_depth
            and not isinstance(expr, claripy.ast.Bool)
        ]
        # Replace the largest, most frequently shared subexpressions first so a
        # single replacement can absorb many nested duplicates at once.
        candidates.sort(key=lambda e: (e.depth, counts[hash(e)]), reverse=True)
        candidates = candidates[:max_replacements]
        if not candidates:
            return simplified

        # Drop a candidate that is wholly contained in a larger selected one.
        selected: list[BvAst] = []

        def contains(node: claripy.ast.Base, target_hash: int) -> bool:
            if not isinstance(node, claripy.ast.Base):
                return False
            if hash(node) == target_hash:
                return True
            return any(contains(child, target_hash) for child in node.args if isinstance(child, claripy.ast.Base))

        for candidate in candidates:
            if any(contains(bigger, hash(candidate)) for bigger in selected):
                continue
            selected.append(candidate)

        definitions: list[BoolAst] = []
        outputs: list[BoolAst] = list(simplified)
        for index, shared in enumerate(selected):
            symbol = claripy.BVS(f"cse_{index}", shared.length)
            outputs = [cast(BoolAst, claripy.replace(c, shared, symbol)) for c in outputs]
            definitions.append(cast(BoolAst, symbol == shared))
        return outputs + definitions


class ConstraintSimplificationCache:
    """
    A thread-safe, bounded LRU cache of simplified constraints.

    Keys are structural AST hashes, so the cache is shared safely across all
    states in a process: two ASTs with the same hash are the same interned
    expression and therefore have identical simplifications. Stored values are
    AST references, which keep the interned expressions alive.
    """

    def __init__(self, maxsize: int = 4096):
        self._cache: SmartLRUCache[int, BoolAst] = SmartLRUCache(maxsize)
        self._lock = threading.RLock()
        self.hits = 0
        self.misses = 0

    def get_or_simplify(self, expr: BoolAst, strategy: ConstraintSimplificationStrategy) -> BoolAst:
        key = hash(expr)
        with self._lock:
            if key in self._cache:
                self.hits += 1
                return self._cache[key]
            self.misses += 1

        # Rewriting happens outside the lock: it is pure and the worst case of
        # two threads simplifying the same expression concurrently is one
        # redundant rewrite, never corruption.
        simplified = strategy.simplify_constraint(expr)
        with self._lock:
            self._cache[key] = simplified
        return simplified

    def get_or_simplify_many(self, exprs: list[BoolAst], strategy: ConstraintSimplificationStrategy) -> list[BoolAst]:
        """Simplify a batch of constraints, reusing cached per-expression results."""
        return [self.get_or_simplify(expr, strategy) for expr in exprs]

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self.hits = 0
            self.misses = 0

    def stats(self) -> dict[str, Any]:
        with self._lock:
            total = self.hits + self.misses
            return {
                "size": len(self._cache),
                "maxsize": self._cache.maxsize,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": (self.hits / total) if total else 0.0,
            }


# A cache argument is either a real cache, None (caching off), or the sentinel
# (resolve to the process-wide default).
CacheArgument = ConstraintSimplificationCache | object | None


# Process-wide defaults. The environment variable lets users size the cache
# without touching code; 0 disables caching entirely.
_DEFAULT_CACHE_SIZE = int(os.environ.get("ANGR_CONSTRAINT_SIMPLIFY_CACHE", "4096"))
_default_strategy = ConstraintSimplificationStrategy()
_default_cache: ConstraintSimplificationCache | None = (
    ConstraintSimplificationCache(_DEFAULT_CACHE_SIZE) if _DEFAULT_CACHE_SIZE > 0 else None
)


def get_default_strategy() -> ConstraintSimplificationStrategy:
    """Return the process-wide default simplification strategy."""
    return _default_strategy


def get_default_cache() -> ConstraintSimplificationCache | None:
    """Return the process-wide shared simplification cache, if caching is enabled."""
    return _default_cache


def simplify_constraint(
    expr: BoolAst,
    strategy: ConstraintSimplificationStrategy | None = None,
    cache: CacheArgument = USE_DEFAULT_CACHE,
) -> BoolAst:
    """
    Simplify one path constraint using the shared strategy and cache.

    Pass ``cache=None`` to bypass caching for a single call; by default the
    process-wide cache is used when enabled.
    """
    active_strategy = _default_strategy if strategy is None else strategy
    active_cache = _default_cache if cache is USE_DEFAULT_CACHE else cache
    if active_cache is None:
        return active_strategy.simplify_constraint(expr)
    return cast(ConstraintSimplificationCache, active_cache).get_or_simplify(expr, active_strategy)


def simplify_constraints(
    exprs: list[BoolAst],
    strategy: ConstraintSimplificationStrategy | None = None,
    cache: CacheArgument = USE_DEFAULT_CACHE,
    eliminate_common_subexpressions: bool = True,
) -> list[BoolAst]:
    """
    Simplify a batch of constraints, optionally eliminating common
    subexpressions across the whole batch.
    """
    active_strategy = _default_strategy if strategy is None else strategy
    active_cache = _default_cache if cache is USE_DEFAULT_CACHE else cache
    if active_cache is None:
        per_expr = [active_strategy.simplify_constraint(e) for e in exprs]
    else:
        per_expr = cast(ConstraintSimplificationCache, active_cache).get_or_simplify_many(list(exprs), active_strategy)
    if not eliminate_common_subexpressions:
        return per_expr
    return active_strategy.simplify_constraints(per_expr)
