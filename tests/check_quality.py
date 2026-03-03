#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quality checks for the push_scope deprecation change.

Checks:
  1. CHANGELOG.md contains an entry describing the push_scope deprecation warning.
  2. sentry_sdk.push_scope docstring mentions that it is deprecated.
  3. The DeprecationWarning uses correct stacklevel so it points to the caller.
  4. Public API: sentry_sdk.push_scope is exported at the top level with a
     type annotation (verified via __annotations__ or inspect).

Run directly:  python tests/check_quality.py
Exit code 0 = all checks pass, non-zero = at least one check failed.
"""

import inspect
import os
import sys
import warnings

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PASS = "\u2713 PASS"
FAIL = "\u2717 FAIL"
results = []


def check(name: str, passed: bool, detail: str = "") -> None:
    status = PASS if passed else FAIL
    msg = f"[{status}] {name}"
    if detail:
        msg += f"\n       {detail}"
    print(msg)
    results.append(passed)


# ---------------------------------------------------------------------------
# Locate repo root (two levels up from this file: tests/ -> repo root)
# ---------------------------------------------------------------------------

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TESTS_DIR)

# ---------------------------------------------------------------------------
# 1. CHANGELOG check
# ---------------------------------------------------------------------------

changelog_path = os.path.join(REPO_ROOT, "CHANGELOG.md")

try:
    with open(changelog_path, encoding="utf-8") as f:
        changelog_text = f.read()

    # We want to find a NEW entry that says push_scope now emits/raises a
    # DeprecationWarning. The existing CHANGELOG already mentions push_scope
    # is deprecated (soft-deprecation prose), but does NOT mention the actual
    # Python DeprecationWarning class. The model must add such an entry.
    lines = changelog_text.splitlines()
    found_warning_entry = False
    for i, line in enumerate(lines):
        window = "\n".join(lines[max(0, i - 4): i + 5])
        # Require 'push_scope' AND 'DeprecationWarning' in the same 9-line window
        if "push_scope" in window and "DeprecationWarning" in window:
            found_warning_entry = True
            break

    check(
        "CHANGELOG.md contains a push_scope DeprecationWarning entry",
        found_warning_entry,
        detail=(
            "Expected a CHANGELOG entry that mentions both 'push_scope' and "
            "'DeprecationWarning' within the same section. "
            "Please add an entry describing that push_scope now emits a DeprecationWarning."
        ) if not found_warning_entry else "",
    )
except FileNotFoundError:
    check(
        "CHANGELOG.md exists",
        False,
        detail=f"File not found: {changelog_path}",
    )

# ---------------------------------------------------------------------------
# 2. Docstring check
# ---------------------------------------------------------------------------

try:
    # Add repo root to path so we can import sentry_sdk from source
    if REPO_ROOT not in sys.path:
        sys.path.insert(0, REPO_ROOT)

    from sentry_sdk import push_scope as _ps  # noqa: E402

    docstring = inspect.getdoc(_ps) or ""
    docstring_lower = docstring.lower()
    mentions_deprecated = "deprecated" in docstring_lower or "deprecationwarning" in docstring_lower

    check(
        "push_scope docstring mentions that it is deprecated",
        mentions_deprecated,
        detail=(
            f"Docstring does not contain 'deprecated' or 'DeprecationWarning'.\n"
            f"       Current docstring:\n"
            + "\n".join(f"       | {line}" for line in docstring.splitlines())
        ) if not mentions_deprecated else "",
    )
except Exception as exc:
    check(
        "push_scope docstring check",
        False,
        detail=f"Import or inspection failed: {exc}",
    )

# ---------------------------------------------------------------------------
# 3. Correct stacklevel – warning must point to caller, not sentry_sdk/api.py
# ---------------------------------------------------------------------------

try:
    from sentry_sdk import push_scope as _ps2  # noqa: E402 (same object, re-imported for clarity)

    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        with _ps2():
            pass

    deprecation_warnings = [w for w in recorded if issubclass(w.category, DeprecationWarning)]

    if not deprecation_warnings:
        check(
            "DeprecationWarning stacklevel points to caller",
            False,
            detail="No DeprecationWarning was raised at all – fix push_scope first.",
        )
    else:
        warning_filename = deprecation_warnings[0].filename
        points_to_api = os.path.basename(warning_filename) == "api.py"
        check(
            "DeprecationWarning stacklevel points to caller (not api.py)",
            not points_to_api,
            detail=(
                f"Warning filename is {warning_filename!r}. "
                "It should point to the call site, not to sentry_sdk/api.py. "
                "Set stacklevel=2 (or higher) in warnings.warn()."
            ) if points_to_api else "",
        )
except Exception as exc:
    check(
        "DeprecationWarning stacklevel check",
        False,
        detail=f"Unexpected error: {exc}",
    )

# ---------------------------------------------------------------------------
# 4. Public API type annotation – push_scope re-exported from top-level
#    sentry_sdk with proper overload annotations in sentry_sdk/api.py
# ---------------------------------------------------------------------------

try:
    import sentry_sdk as sdk

    # Verify push_scope is accessible at top level
    has_push_scope_attr = hasattr(sdk, "push_scope")

    # Verify the source file has overload decorators for push_scope
    api_path = os.path.join(REPO_ROOT, "sentry_sdk", "api.py")
    with open(api_path, encoding="utf-8") as f:
        api_source = f.read()

    has_overload = "@overload" in api_source and "push_scope" in api_source

    check(
        "push_scope is exported from sentry_sdk top-level module",
        has_push_scope_attr,
        detail="sentry_sdk.push_scope not found in the top-level namespace." if not has_push_scope_attr else "",
    )

    check(
        "push_scope has @overload type annotations in sentry_sdk/api.py",
        has_overload,
        detail=(
            "Could not find @overload annotations for push_scope in sentry_sdk/api.py. "
            "Ensure the function retains its type-annotated overloads after the change."
        ) if not has_overload else "",
    )
except Exception as exc:
    check(
        "Public API type annotation check",
        False,
        detail=f"Unexpected error: {exc}",
    )

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print()
print(f"Results: {sum(results)}/{len(results)} checks passed.")

if all(results):
    print("All quality checks passed!")
    sys.exit(0)
else:
    failed = len(results) - sum(results)
    print(f"{failed} check(s) failed. See above for details.")
    sys.exit(1)
