import pytest

from prism.diffs import decode_diff_upload, parse_unified_diff
from prism.inputs import InputError, MAX_BYTES


def test_parse_unified_diff_collects_added_lines_and_safe_basename():
    diff = """diff --git a/src/example.py b/src/example.py
index 1234567..abcdef0 100644
--- a/src/example.py
+++ b/src/example.py
@@ -1,3 +1,4 @@
 import os
-print("old")
+exec("new")
 x = 1
+import sys
"""

    spec = parse_unified_diff(diff)

    assert spec.file_path == "example.py"
    assert spec.changed_lines == frozenset({2, 4})


def test_parse_new_file_hunk_with_zero_old_lines():
    spec = parse_unified_diff(
        """diff --git a/new.py b/new.py
new file mode 100644
--- /dev/null
+++ b/new.py
@@ -0,0 +1,2 @@
+x = 1
+y = 2
"""
    )
    assert spec.file_path == "new.py"
    assert spec.changed_lines == frozenset({1, 2})


def test_parse_unified_diff_rejects_multiple_files():
    diff = """--- a/one.py
+++ b/one.py
@@ -1 +1 @@
-x = 1
+x = 2
--- a/two.py
+++ b/two.py
@@ -1 +1 @@
-y = 1
+y = 2
"""
    with pytest.raises(InputError, match="exactly one file"):
        parse_unified_diff(diff)


def test_parse_unified_diff_rejects_invalid_hunk_counts():
    diff = """--- a/one.py
+++ b/one.py
@@ -1,2 +1,2 @@
-x = 1
+x = 2
"""
    with pytest.raises(InputError, match="incomplete|counts"):
        parse_unified_diff(diff)


def test_parse_unified_diff_rejects_no_added_lines():
    diff = """--- a/one.py
+++ b/one.py
@@ -1 +1,0 @@
-x = 1
"""
    with pytest.raises(InputError, match="no added or changed lines"):
        parse_unified_diff(diff)


def test_parse_unified_diff_rejects_unsafe_paths_and_non_python_files():
    unsafe = """--- a/../../secret.py
+++ b/../../secret.py
@@ -1 +1 @@
-x = 1
+x = 2
"""
    with pytest.raises(InputError, match="unsafe file path"):
        parse_unified_diff(unsafe)

    non_python = """--- a/notes.txt
+++ b/notes.txt
@@ -1 +1 @@
-x
+y
"""
    with pytest.raises(InputError, match="only .py"):
        parse_unified_diff(non_python)


def test_decode_diff_upload_checks_extension_encoding_and_size():
    with pytest.raises(InputError, match=".diff or .patch"):
        decode_diff_upload(b"diff", "changes.txt")
    with pytest.raises(InputError, match="UTF-8"):
        decode_diff_upload(b"\xff", "changes.diff")
    with pytest.raises(InputError, match="200,000-byte limit"):
        decode_diff_upload(b" " * (MAX_BYTES + 1), "changes.patch")
