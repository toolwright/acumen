"""Tests for lib/classify.py -- Tier 0.5 field derivation."""

from lib.classify import (
    classify_command_family,
    classify_command_signature,
    classify_file_basename,
    classify_path_pattern,
    classify_write_kind,
    classify_environment_tag,
    classify_error_class,
)


# -- command_family --


def test_command_family_python():
    assert classify_command_family("Bash", "python foo.py") == "python"
    assert classify_command_family("Bash", "python3 script.py") == "python"


def test_command_family_node():
    assert classify_command_family("Bash", "npm install") == "node"
    assert classify_command_family("Bash", "npx tsc") == "node"
    assert classify_command_family("Bash", "node server.js") == "node"


def test_command_family_git():
    assert classify_command_family("Bash", "git status") == "git"
    assert classify_command_family("Bash", "git commit -m 'msg'") == "git"


def test_command_family_test():
    assert classify_command_family("Bash", "pytest tests/ -v") == "test"
    assert classify_command_family("Bash", "jest --watch") == "test"
    assert classify_command_family("Bash", "cargo test") == "test"
    assert classify_command_family("Bash", "go test ./...") == "test"


def test_command_family_build():
    assert classify_command_family("Bash", "make build") == "build"
    assert classify_command_family("Bash", "cargo build") == "build"
    assert classify_command_family("Bash", "npm run build") == "build"


def test_command_family_lint():
    assert classify_command_family("Bash", "ruff check .") == "lint"
    assert classify_command_family("Bash", "eslint src/") == "lint"
    assert classify_command_family("Bash", "mypy lib/") == "lint"


def test_command_family_format():
    assert classify_command_family("Bash", "ruff format .") == "format"
    assert classify_command_family("Bash", "black .") == "format"
    assert classify_command_family("Bash", "prettier --write .") == "format"


def test_command_family_docker():
    assert classify_command_family("Bash", "docker build .") == "docker"
    assert classify_command_family("Bash", "docker-compose up") == "docker"


def test_command_family_shell():
    assert classify_command_family("Bash", "ls -la") == "shell"
    assert classify_command_family("Bash", "cat foo.txt") == "shell"
    assert classify_command_family("Bash", "mkdir -p dir") == "shell"


def test_command_family_non_bash():
    """Non-Bash tools return None for command_family."""
    assert classify_command_family("Read", "") is None
    assert classify_command_family("Edit", "") is None
    assert classify_command_family("Write", "/path/to/file") is None


def test_command_family_empty_command():
    assert classify_command_family("Bash", "") is None
    assert classify_command_family("Bash", None) is None


def test_command_family_uv_run():
    """uv run pytest should be test, not shell."""
    assert classify_command_family("Bash", "uv run pytest tests/") == "test"


def test_command_family_python_m_pytest():
    """python -m pytest is test, not python."""
    assert classify_command_family("Bash", "python3 -m pytest tests/ -v") == "test"
    assert classify_command_family("Bash", "python -m pytest") == "test"


# -- command_signature --


def test_signature_pytest():
    assert classify_command_signature("Bash", "pytest tests/ -v") == "pytest"
    assert classify_command_signature("Bash", "python3 -m pytest tests/") == "pytest"
    assert classify_command_signature("Bash", "python -m pytest") == "pytest"


def test_signature_uv_pytest():
    assert classify_command_signature("Bash", "uv run pytest tests/") == "uv_pytest"


def test_signature_npm_test():
    assert classify_command_signature("Bash", "npm test") == "npm_test"


def test_signature_jest():
    assert classify_command_signature("Bash", "npx jest --watch") == "jest"
    assert classify_command_signature("Bash", "jest tests/") == "jest"


def test_signature_cargo_test():
    assert classify_command_signature("Bash", "cargo test") == "cargo_test"


def test_signature_go_test():
    assert classify_command_signature("Bash", "go test ./...") == "go_test"


def test_signature_ruff_check():
    assert classify_command_signature("Bash", "ruff check .") == "ruff_check"


def test_signature_ruff_format():
    assert classify_command_signature("Bash", "ruff format .") == "ruff_format"


def test_signature_none_for_non_test():
    """Non-test/lint/format commands return None."""
    assert classify_command_signature("Bash", "git status") is None
    assert classify_command_signature("Bash", "ls -la") is None
    assert classify_command_signature("Bash", "python foo.py") is None


def test_signature_non_bash():
    assert classify_command_signature("Read", "") is None


# -- file_basename --


def test_file_basename_write():
    assert classify_file_basename("Write", "/Users/tom/project/lib/foo.py") == "foo.py"


def test_file_basename_edit():
    assert classify_file_basename("Edit", "/Users/tom/project/tests/test_bar.py") == "test_bar.py"


def test_file_basename_read():
    assert classify_file_basename("Read", "/opt/project/README.md") == "README.md"


def test_file_basename_non_file_tool():
    assert classify_file_basename("Bash", "/some/path") is None
    assert classify_file_basename("Bash", "") is None


def test_file_basename_no_path():
    assert classify_file_basename("Write", "") is None
    assert classify_file_basename("Edit", None) is None


# -- path_pattern --


def test_path_pattern_tests_root():
    assert classify_path_pattern("Write", "/project/tests/test_foo.py") == "tests_root"
    assert classify_path_pattern("Edit", "/project/tests/unit/test_bar.py") == "tests_root"


def test_path_pattern_integration_dir():
    assert classify_path_pattern("Write", "/project/integration/test_e2e.py") == "integration_dir"


def test_path_pattern_src_dir():
    assert classify_path_pattern("Write", "/project/src/module.py") == "src_dir"


def test_path_pattern_lib_dir():
    assert classify_path_pattern("Edit", "/project/lib/classify.py") == "lib_dir"


def test_path_pattern_non_write_edit():
    """Only Write/Edit tools get path_pattern."""
    assert classify_path_pattern("Read", "/project/tests/test_foo.py") is None
    assert classify_path_pattern("Bash", "/project/src/foo.py") is None


def test_path_pattern_no_path():
    assert classify_path_pattern("Write", "") is None
    assert classify_path_pattern("Write", None) is None


def test_path_pattern_unknown():
    """Paths that don't match known patterns return None."""
    assert classify_path_pattern("Write", "/project/foo.py") is None


# -- write_kind --


def test_write_kind_write_new(tmp_path):
    """Write tool on a non-existent file → 'create'."""
    path = str(tmp_path / "new_file.py")
    assert classify_write_kind("Write", path) == "create"


def test_write_kind_write_existing(tmp_path):
    """Write tool on an existing file → 'edit'."""
    existing = tmp_path / "existing.py"
    existing.write_text("content")
    assert classify_write_kind("Write", str(existing)) == "edit"


def test_write_kind_edit_always():
    """Edit tool always returns 'edit'."""
    assert classify_write_kind("Edit", "/any/path.py") == "edit"


def test_write_kind_other_tools():
    assert classify_write_kind("Read", "/some/file.py") is None
    assert classify_write_kind("Bash", "") is None


def test_write_kind_no_path():
    assert classify_write_kind("Write", "") is None
    assert classify_write_kind("Write", None) is None


# -- environment_tag --


def test_environment_tag_python(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]")
    assert classify_environment_tag(tmp_path) == "python"


def test_environment_tag_python_setup_py(tmp_path):
    (tmp_path / "setup.py").write_text("setup()")
    assert classify_environment_tag(tmp_path) == "python"


def test_environment_tag_node(tmp_path):
    (tmp_path / "package.json").write_text("{}")
    assert classify_environment_tag(tmp_path) == "node"


def test_environment_tag_rust(tmp_path):
    (tmp_path / "Cargo.toml").write_text("[package]")
    assert classify_environment_tag(tmp_path) == "rust"


def test_environment_tag_go(tmp_path):
    (tmp_path / "go.mod").write_text("module example.com")
    assert classify_environment_tag(tmp_path) == "go"


def test_environment_tag_none(tmp_path):
    assert classify_environment_tag(tmp_path) is None


def test_environment_tag_python_over_node(tmp_path):
    """When both exist, python wins (checked first)."""
    (tmp_path / "pyproject.toml").write_text("[project]")
    (tmp_path / "package.json").write_text("{}")
    assert classify_environment_tag(tmp_path) == "python"


# -- error_class --


def test_error_class_command_not_found():
    assert classify_error_class("tool_failure", "command not found: python") == "command_not_found"
    assert classify_error_class("tool_failure", "zsh: command not found: foo") == "command_not_found"


def test_error_class_file_not_found():
    assert classify_error_class("tool_failure", "No such file or directory") == "file_not_found"
    assert classify_error_class("tool_error", "FileNotFoundError: foo.py") == "file_not_found"


def test_error_class_permission_denied():
    assert classify_error_class("tool_failure", "Permission denied") == "permission_denied"
    assert classify_error_class("tool_failure", "EACCES: permission denied") == "permission_denied"


def test_error_class_syntax_error():
    assert classify_error_class("tool_failure", "SyntaxError: invalid syntax") == "syntax_error"
    assert classify_error_class("tool_failure", "bash: syntax error near") == "syntax_error"


def test_error_class_timeout():
    assert classify_error_class("tool_failure", "command timed out") == "timeout"
    assert classify_error_class("tool_failure", "TimeoutError") == "timeout"


def test_error_class_test_failure():
    assert classify_error_class("tool_failure", "FAILED tests/test_foo.py") == "test_failure"
    assert classify_error_class("tool_failure", "1 failed, 3 passed") == "test_failure"


def test_error_class_no_error():
    assert classify_error_class(None, None) is None
    assert classify_error_class(None, "") is None


def test_error_class_unknown_error():
    """Error type present but message doesn't match known classes → unclassified."""
    assert classify_error_class("tool_failure", "some random error") == "unclassified"


def test_error_class_no_message():
    """Error type present but no message → unclassified (not None)."""
    assert classify_error_class("tool_failure", None) == "unclassified"
    assert classify_error_class("tool_failure", "") == "unclassified"


def test_error_class_exit_code_127():
    """Exit code 127 = command not found."""
    assert classify_error_class("tool_failure", "exit code 127") == "command_not_found"


# -- user_denied --


def test_error_class_user_denied():
    """User denial of tool use → user_denied."""
    assert classify_error_class("tool_failure", "denied by user") == "user_denied"
    assert classify_error_class("tool_failure", "User denied tool use") == "user_denied"
    assert classify_error_class("tool_failure", "tool use was denied") == "user_denied"


def test_error_class_user_denied_not_filesystem():
    """Filesystem 'permission denied' should NOT match user_denied."""
    assert classify_error_class("tool_failure", "Permission denied") == "permission_denied"
    assert classify_error_class("tool_failure", "EACCES: permission denied") == "permission_denied"
