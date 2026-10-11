# Core 1.2 stage 1: exhaustive wheel and candidate API inventory

!!! warning "Inventory is not qualification"
    The generated artifact lists every file in the built wheel, all packaged Python
    module paths, static public class/function/import declarations, and the root
    `__all__` exports. This is an **exhaustive structural inventory**, not
    an approved or semantically validated API freeze.

This tranche is stacked on [core-only stage 0 PR #283](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/283)
and isolated from protected `main`. It builds the actual `1.2.0rc2.dev0`
development wheel and compares *every packaged .py file by both path and SHA256*
with the exact source Python files. Missing modules, extra modules, mismatched
bytes or unqualified `eyetrajectoriespy.bayesian` and
`eyetrajectoriespy.research` modules fail closed. Unexpected top-level source
tools are rejected. Files such as `py.typed`, metadata, and any non-Python
package data are captured as wheel file entries with per-entry digests.

The published `v1.1.0` source-tag root `__all__` provides a separate
**458-name immutable comparison baseline**. This verifies that the new core
wheel has no additions or removals in the explicitly declared root export
names; it does **not** verify signatures, semantics, downstream import behavior
or scientific correctness. Any deliberate change must be independently
reviewed and versioned before updating this baseline.

The AST-based symbol catalog records direct public functions/classes/imported
symbols on each packaged module. Python submodules remain technically
importable even when absent from the public root. The report categorizes those
as **review required**, not implicitly supported. Explicit root `__all__`
exports are fully enumerated and hashed. Dynamic attributes and
runtime-generated exports may require separate manual inspection.

## Outstanding core qualification

An independent reviewer must classify each installed module and top-level
public symbol as supported, private/internal, explicitly experimental or
excluded; verify experimental names under non-root submodule imports; freeze
the approved root and submodule API signatures; review documentation claims;
and qualify their numerical contracts. Then issue #225 may proceed to a
**separate literal 1.2.0rc2 version** with new exact-version evidence on a
fresh candidate head and on protected main. Neither RC2 nor its publication
is authorized here. Source version remains `1.2.0rc2.dev0`.

The [Bayesian #255](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/255),
[F5 #256](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/256)
and [F1–F6 #226](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/226)
scientific gates remain open. R5 research stays separately stacked on R4.
