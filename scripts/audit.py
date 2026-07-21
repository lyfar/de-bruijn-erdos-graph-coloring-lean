#!/usr/bin/env python3
"""Build the project and audit proof gaps, warnings, and axiom dependencies."""

from pathlib import Path
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
LIBRARY_SOURCES = [
    ROOT / "DeBruijnErdosGraphColoring.lean",
    *sorted((ROOT / "DeBruijnErdosGraphColoring").glob("**/*.lean")),
]
FORBIDDEN = re.compile(
    r"\b(?:sorry|admit|axiom|unsafe|partial|opaque|native_decide)\b"
    r"|@\[\s*extern\b|\bset_option\b|\bnolint\b"
)
ALLOWED_AXIOMS = {"Classical.choice", "propext", "Quot.sound"}
AUDITED_DECLARATIONS = [
    "Finset.rado_selection_constraints",
    "SimpleGraph.nonempty_hom_of_finite_induced",
    "SimpleGraph.nonempty_hom_iff_finite_induced",
    "SimpleGraph.not_nonempty_hom_iff_exists_finite_induced",
    "SimpleGraph.nonempty_coloring_of_finite_induced",
    "SimpleGraph.nonempty_coloring_iff_finite_induced",
    "SimpleGraph.not_nonempty_coloring_iff_exists_finite_induced",
    "SimpleGraph.colorable_of_finite_induced_colorable",
    "SimpleGraph.finite_induced_colorable_of_colorable",
    "SimpleGraph.colorable_iff_finite_induced_colorable",
    "SimpleGraph.not_colorable_iff_exists_finite_induced_not_colorable",
    "SimpleGraph.ListColoring.induce",
    "SimpleGraph.nonempty_listColoring_of_finite_induced",
    "SimpleGraph.nonempty_listColoring_iff_finite_induced",
    "SimpleGraph.not_nonempty_listColoring_iff_exists_finite_induced",
    "SimpleGraph.succ_le_chromaticNumber_iff_not_colorable",
    "SimpleGraph.succ_le_chromaticNumber_iff_exists_finite_induced",
    "SimpleGraph.exists_finite_induced_chromaticNumber_eq",
    "SimpleGraph.chromaticNumber_ne_top_iff_exists_uniform_finite_induced_colorable",
    "SimpleGraph.chromaticNumber_eq_top_iff_forall_exists_finite_induced_not_colorable",
    "SimpleGraph.chromaticNumber_eq_top_iff_forall_exists_finite_induced_succ_le",
]


def run(*command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    for source in LIBRARY_SOURCES:
        match = FORBIDDEN.search(source.read_text(encoding="utf-8"))
        if match:
            fail(f"{source.relative_to(ROOT)} contains forbidden token: {match.group(0)}")

    build = run("lake", "build", "DeBruijnErdosGraphColoring")
    print(build.stdout, end="")
    print(build.stderr, end="", file=sys.stderr)
    if build.returncode:
        fail("build failed")
    if "warning:" in (build.stdout + build.stderr).lower():
        fail("build emitted a warning")

    audit_source = "import DeBruijnErdosGraphColoring\n\n" + "\n".join(
        f"#print axioms {declaration}" for declaration in AUDITED_DECLARATIONS
    )
    with tempfile.NamedTemporaryFile(
        "w", suffix=".lean", encoding="utf-8", delete=False
    ) as audit_file:
        audit_file.write(audit_source)
        audit_path = Path(audit_file.name)
    try:
        audit = run("lake", "env", "lean", str(audit_path))
    finally:
        audit_path.unlink(missing_ok=True)
    print(audit.stdout, end="")
    print(audit.stderr, end="", file=sys.stderr)
    if audit.returncode:
        fail("axiom audit failed")

    output = audit.stdout + audit.stderr
    reports = re.findall(r"depends on axioms:\s*\[([^]]*)\]", output, flags=re.DOTALL)
    report_count = len(reports) + output.count("does not depend on any axioms")
    expected_audits = len(AUDITED_DECLARATIONS)
    if report_count != expected_audits:
        fail(f"expected {expected_audits} axiom reports, found {report_count}")

    used_axioms: set[str] = set()
    for payload in reports:
        used_axioms.update(
            name.strip() for name in payload.split(",") if name.strip()
        )

    unexpected = used_axioms - ALLOWED_AXIOMS
    if unexpected:
        fail(f"unexpected axioms: {', '.join(sorted(unexpected))}")
    print(f"Axiom audit passed; used subset: {', '.join(sorted(used_axioms))}")


if __name__ == "__main__":
    main()
