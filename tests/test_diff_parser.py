from backend.diff_parser import parse_diff


def test_parse_modified_file_with_line_numbers():
    raw = """diff --git a/app/auth.py b/app/auth.py
index 1..2 100644
--- a/app/auth.py
+++ b/app/auth.py
@@ -8,3 +8,3 @@
 def authenticate(username, password):
-    if user and check_password(password, user.password_hash):
+    if user:
         return create_token(user)
"""

    parsed = parse_diff(raw)

    assert parsed.total_files == 1
    assert parsed.total_additions == 1
    assert parsed.total_deletions == 1
    assert parsed.files[0].path == "app/auth.py"
    assert parsed.files[0].hunks[0].added_lines[0].line_number == 9
    assert parsed.files[0].hunks[0].removed_lines[0].line_number == 9
