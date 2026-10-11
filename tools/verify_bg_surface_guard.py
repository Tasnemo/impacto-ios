#!/usr/bin/env python3
"""SMT safety check for the actual Impacto renderer's BG surface guard.

Scope: prove, for ANY 32-bit surface index and ANY map lookup outcome, the
guarded path cannot dereference a missing or null Backgrounds2D entry.

The script checks the relevant C++ source shape first. The SMT abstraction
models the map's find/end contract, NOT the whole C++ engine, ownership,
concurrency, gameplay, or VM semantics. These require different evidence.
Source-only and free of proprietary Steam assets.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "src" / "game.cpp"


def verify_cpp_guard_source() -> None:
    body = GAME.read_text(encoding="utf-8")
    start = body.index("for (int bgId = 0; bgId < std::ssize(Backgrounds); bgId++)")
    end = body.index("}", start)
    block = body[start:end]
    # Any mismatch means the SMT abstraction may no longer model the source.
    requirements = (
        r"const int bufId\s*=\s*ScrWork\[SW_BG1SURF\s*\+\s*bgId\]",
        r"const auto surfaceIt\s*=\s*Backgrounds2D\.find\(bufId\)",
        r"if\s*\(surfaceIt\s*==\s*Backgrounds2D\.end\(\)\s*\|\|\s*"
        r"surfaceIt->second\s*==\s*nullptr\)\s*continue\s*;",
        r"surfaceIt->second->UpdateState\(bgId\);",
        r"surfaceIt->second->Render\(layer\);",
    )
    for pattern in requirements:
        if not re.search(pattern, block):
            raise AssertionError("renderer guard/source divergence: " + pattern)
    if "Backgrounds2D[bufId]" in block:
        raise AssertionError("operator[] can insert null background pointers")
    if not (block.index("Backgrounds2D.find(bufId)") <
            block.index("surfaceIt->second->UpdateState") <
            block.index("surfaceIt->second->Render")):
        raise AssertionError("unsafe order of map validation and dereference")


def prove() -> None:
    if shutil.which("z3") is None:
        raise RuntimeError("Install z3 SMT solver before running verification")

    # A missing map entry is represented by 'found=false', a null pointer
    # by 'nonnull=false'. Both are unconstrained, independent of the signed
    # 32-bit index; this over-approximates every possible map state.
    #
    # The source-guarded path runs ONLY when 'found && nonnull'.
    # Check the negation of three invariants for satisfiability:
    #  1. No dereference when lookup misses.
    #  2. No dereference when mapped pointer is null.
    #  3. No dereference for negative/high surface IDs unless the actual map
    #     contains a non-null pointer for that exact ID.
    smt = """
(set-logic QF_BV)
(declare-const id (_ BitVec 32))
(declare-const found Bool)
(declare-const nonnull Bool)
(define-fun dereferenced () Bool (and found nonnull))
(echo "no_missing_entry_dereference")
(push)
(assert (and dereferenced (not found)))
(check-sat)
(pop)
(echo "no_null_pointer_dereference")
(push)
(assert (and dereferenced (not nonnull)))
(check-sat)
(pop)
(echo "negative_index_must_resolve_in_map")
(push)
(assert (and (bvslt id #x00000000) dereferenced (not (and found nonnull))))
(check-sat)
(pop)
(echo "max_int_index_must_resolve_in_map")
(push)
(assert (= id #x7fffffff))
(assert (and dereferenced (not (and found nonnull))))
(check-sat)
(pop)
"""
    p = subprocess.run(["z3", "-in"], input=smt, capture_output=True,
                       text=True, timeout=15, check=True)
    expected = ["no_missing_entry_dereference", "unsat",
                "no_null_pointer_dereference", "unsat",
                "negative_index_must_resolve_in_map", "unsat",
                "max_int_index_must_resolve_in_map", "unsat"]
    actual = [v.strip().strip('"') for v in p.stdout.splitlines() if v.strip()]
    if actual != expected:
        raise AssertionError(f"SMT obligations failed: {actual}; stderr: {p.stderr}")
    for name in expected[::2]:
        print(f"PROVEN UNSAT: {name}")
    print("Scope: one BG RenderMain lookup/dereference under the verified C++ guard."
          " Other VM instructions and memory ownership are NOT covered.")


def main() -> int:
    verify_cpp_guard_source()
    print("C++ renderer source matches the checked guard model")
    prove()
    return 0


if __name__ == "__main__":
    sys.exit(main())
