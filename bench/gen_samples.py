#!/usr/bin/env python3
"""Generate 50 diverse C samples for the path-constraint simplification benchmark.

Each program reads symbolic input, builds path constraints through a mix of
branches, loops, switches and bitwise arithmetic, and ends in a distinguishable
sink. The generator is deterministic so the corpus is reproducible.
"""

from __future__ import annotations

import random
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
BIN = ROOT / "bin"
N = 50

CMP = ["<", ">", "<=", ">=", "==", "!="]
BINOPS = ["+", "-", "*", "&", "|", "^", "<<", ">>"]


def emit_branch(rng, depth: int, idx: int) -> str:
    if depth == 0:
        return f"    sink = {idx} % 7;\n"
    var = rng.choice(["a", "b", "c", "d"])
    op = rng.choice(CMP)
    rhs = rng.randint(1, 60)
    other = rng.choice(BINOPS)
    cond = f"({var} {op} {rhs})"
    if rng.random() < 0.4:
        cond = f"(({var} {other} {rng.randint(1, 15)}) {op} {rhs})"
    then_branch = emit_branch(rng, depth - 1, idx + 1)
    else_branch = emit_branch(rng, depth - 1, idx + 7)
    return f"    if {cond} {{\n{then_branch}    }} else {{\n{else_branch}    }}\n"


def emit_loop(rng, idx: int) -> str:
    bound = rng.randint(2, 5)
    var = rng.choice(["a", "b", "c"])
    acc = rng.choice(["e", "f"])
    op = rng.choice(BINOPS)
    return (
        f"    for (int i = 0; i < {bound}; i++) {{\n"
        f"        if (({var} + i) {rng.choice(CMP)} {rng.randint(1, 40)}) {{\n"
        f"            {acc} = {acc} {op} ({var} ^ i);\n"
        f"        }}\n"
        f"    }}\n"
        f"    sink = {acc} & 0xff;\n"
    )


def emit_switch(rng, idx: int) -> str:
    var = rng.choice(["a", "b"])
    n = rng.randint(3, 5)
    lines = [f"    switch ({var} & 0x7) {{"]
    for k in range(n):
        lines.append(f"      case {k}: sink = {var} {rng.choice(BINOPS)} {k}; break;")
    lines.append("      default: sink = -1;")
    lines.append("    }")
    return "\n".join(lines) + "\n"


def emit_mixed(rng, idx: int) -> str:
    parts = [emit_branch(rng, 2, idx)]
    if rng.random() < 0.6:
        parts.append(emit_loop(rng, idx))
    if rng.random() < 0.5:
        parts.append(emit_switch(rng, idx))
    return "".join(parts)


TEMPLATES = {
    "branch": emit_branch,
    "loop": emit_loop,
    "switch": emit_switch,
    "mixed": emit_mixed,
}


def main() -> None:
    SRC.mkdir(exist_ok=True)
    BIN.mkdir(exist_ok=True)
    rng = random.Random(20261123)
    kinds = list(TEMPLATES)
    for i in range(N):
        kind = kinds[i % len(kinds)]
        rng_local = random.Random(rng.randint(0, 2**31))
        if kind == "branch":
            body = emit_branch(rng_local, rng_local.choice([3, 4, 5]), i)
        elif kind == "loop":
            body = emit_loop(rng_local, i)
        elif kind == "switch":
            body = emit_switch(rng_local, i)
        else:
            body = emit_mixed(rng_local, i)
        src = f"""#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
int main(void) {{
    unsigned int a = 0, b = 0, c = 0, d = 0;
    unsigned int e = 0, f = 0;
    int sink = 0;
    unsigned char buf[16];
    if (read(0, buf, sizeof(buf)) <= 0) return 1;
    a = (buf[0] << 8) | buf[1];
    b = (buf[2] << 8) | buf[3];
    c = (buf[4] << 8) | buf[5];
    d = (buf[6] << 8) | buf[7];
{body}
    printf("%d\\n", sink);
    return 0;
}}
"""
        src_path = SRC / f"sample_{i:02d}_{kind}.c"
        bin_path = BIN / f"sample_{i:02d}_{kind}"
        src_path.write_text(src)
        subprocess.run(
            ["gcc", "-O0", "-fno-stack-protector", "-o", str(bin_path), str(src_path)],
            check=True,
        )
    print(f"generated {N} samples in {BIN}")


if __name__ == "__main__":
    main()
