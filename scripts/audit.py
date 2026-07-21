#!/usr/bin/env python3
"""Build the project and audit proof gaps, warnings, and axiom dependencies."""

from pathlib import Path
import re
import subprocess
import sys


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
EXPECTED_AUDITS = 21


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

    audit = run("lake", "env", "lean", "AxiomAudit.lean")
    print(audit.stdout, end="")
    print(audit.stderr, end="", file=sys.stderr)
    if audit.returncode:
        fail("axiom audit failed")

    output = audit.stdout + audit.stderr
    reports = re.findall(r"depends on axioms:\s*\[([^]]*)\]", output, flags=re.DOTALL)
    report_count = len(reports) + output.count("does not depend on any axioms")
    if report_count != EXPECTED_AUDITS:
        fail(f"expected {EXPECTED_AUDITS} axiom reports, found {report_count}")

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
