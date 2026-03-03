"""
Tests to verify that sentry_sdk.push_scope emits a DeprecationWarning
when called, with correct message and behaviour.

These tests should FAIL before the fix and PASS after the fix.
"""

import warnings
import pytest
import sentry_sdk
from sentry_sdk import push_scope


# ---------------------------------------------------------------------------
# 1. Context-manager form emits DeprecationWarning
# ---------------------------------------------------------------------------

def test_push_scope_context_manager_emits_deprecation_warning():
    """Calling push_scope() as a context manager must raise DeprecationWarning."""
    with pytest.warns(DeprecationWarning):
        with push_scope():
            pass


# ---------------------------------------------------------------------------
# 2. Callback form emits DeprecationWarning
# ---------------------------------------------------------------------------

def test_push_scope_callback_emits_deprecation_warning():
    """Calling push_scope(callback=...) must raise DeprecationWarning."""
    called = []

    def callback(scope):
        called.append(True)

    with pytest.warns(DeprecationWarning):
        push_scope(callback=callback)

    assert called, "callback should have been invoked"


# ---------------------------------------------------------------------------
# 3. Warning message content – must mention the migration guide URL
# ---------------------------------------------------------------------------

def test_push_scope_warning_message_contains_migration_url():
    """The deprecation warning message must include the migration guide URL."""
    migration_url = "https://docs.sentry.io/platforms/python/migration/1.x-to-2.x"

    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        with push_scope():
            pass

    deprecation_warnings = [
        w for w in recorded if issubclass(w.category, DeprecationWarning)
    ]
    assert deprecation_warnings, "No DeprecationWarning was raised"
    warning_message = str(deprecation_warnings[0].message)
    assert migration_url in warning_message, (
        f"Warning message should contain migration URL '{migration_url}', "
        f"got: {warning_message!r}"
    )


# ---------------------------------------------------------------------------
# 4. Warning message content – must mention push_scope by name
# ---------------------------------------------------------------------------

def test_push_scope_warning_message_mentions_push_scope():
    """The deprecation warning message must mention 'push_scope'."""
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        with push_scope():
            pass

    deprecation_warnings = [
        w for w in recorded if issubclass(w.category, DeprecationWarning)
    ]
    assert deprecation_warnings, "No DeprecationWarning was raised"
    warning_message = str(deprecation_warnings[0].message)
    assert "push_scope" in warning_message, (
        f"Warning message should mention 'push_scope', got: {warning_message!r}"
    )


# ---------------------------------------------------------------------------
# 5. Callback form must emit exactly ONE DeprecationWarning (not two)
# ---------------------------------------------------------------------------

def test_push_scope_callback_emits_exactly_one_warning():
    """
    When push_scope internally recurses to create a scope, the internal
    call must NOT produce an extra deprecation warning. Exactly one warning
    should reach the caller.
    """
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        push_scope(callback=lambda scope: None)

    deprecation_warnings = [
        w for w in recorded if issubclass(w.category, DeprecationWarning)
    ]
    assert len(deprecation_warnings) == 1, (
        f"Expected exactly 1 DeprecationWarning, got {len(deprecation_warnings)}"
    )


# ---------------------------------------------------------------------------
# 6. Context-manager form emits exactly ONE DeprecationWarning
# ---------------------------------------------------------------------------

def test_push_scope_context_manager_emits_exactly_one_warning():
    """A single context-manager call must produce exactly one DeprecationWarning."""
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        with push_scope():
            pass

    deprecation_warnings = [
        w for w in recorded if issubclass(w.category, DeprecationWarning)
    ]
    assert len(deprecation_warnings) == 1, (
        f"Expected exactly 1 DeprecationWarning, got {len(deprecation_warnings)}"
    )


# ---------------------------------------------------------------------------
# 7. Warning stacklevel – the warning should point to the CALLER, not to
#    the internals of sentry_sdk
# ---------------------------------------------------------------------------

def test_push_scope_warning_stacklevel_points_to_caller():
    """
    The DeprecationWarning's filename should point to THIS file (the caller),
    not to sentry_sdk/api.py. This confirms that stacklevel is set correctly.
    """
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        with push_scope():
            pass

    deprecation_warnings = [
        w for w in recorded if issubclass(w.category, DeprecationWarning)
    ]
    assert deprecation_warnings, "No DeprecationWarning was raised"
    warning_filename = deprecation_warnings[0].filename
    assert "api.py" not in warning_filename, (
        f"Warning should point to the caller, not to api.py. "
        f"Got filename: {warning_filename!r}. "
        "This suggests stacklevel is not set correctly."
    )


# ---------------------------------------------------------------------------
# 8. top-level sentry_sdk.push_scope is the same object
# ---------------------------------------------------------------------------

def test_push_scope_accessible_from_top_level_module():
    """sentry_sdk.push_scope should be accessible and emit DeprecationWarning."""
    with pytest.warns(DeprecationWarning):
        with sentry_sdk.push_scope():
            pass


# ---------------------------------------------------------------------------
# 9. The DeprecationWarning category is exactly DeprecationWarning
# ---------------------------------------------------------------------------

def test_push_scope_warning_is_deprecation_warning_category():
    """Warning category must be DeprecationWarning, not a generic Warning."""
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        with push_scope():
            pass

    deprecation_warnings = [
        w for w in recorded if issubclass(w.category, DeprecationWarning)
    ]
    assert deprecation_warnings, "No DeprecationWarning was raised by push_scope()"
    assert deprecation_warnings[0].category is DeprecationWarning, (
        f"Expected category DeprecationWarning, got {deprecation_warnings[0].category}"
    )
