"""Verify architectural boundaries of the modular monolith.
Ensures modules only import from shared or public module interfaces.
"""

import ast
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "lanpad"


def test_no_private_cross_module_imports():
    """Modules must not import internal submodules of other modules directly."""
    modules_dir = SRC / "modules"
    for module_name in os.listdir(modules_dir):
        mod_path = modules_dir / module_name
        if not mod_path.is_dir() or module_name.startswith("__"):
            continue

        for py_file in mod_path.rglob("*.py"):
            tree = ast.parse(py_file.read_text(encoding="utf-8"), str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    # Check for deep imports into other modules
                    parts = node.module.split(".")
                    if "modules" in parts:
                        idx = parts.index("modules")
                        if len(parts) > idx + 2:
                            target_mod = parts[idx + 1]
                            target_sub = parts[idx + 2]
                            if target_mod != module_name and not target_sub.startswith("__"):
                                raise AssertionError(
                                    f"Architecture violation in {py_file}: "
                                    f"Direct internal import of '{node.module}'. "
                                    f"Import from '{target_mod}' public API instead."
                                )


def test_shared_does_not_import_modules():
    """The shared kernel must never import from modules."""
    shared_dir = SRC / "shared"
    for py_file in shared_dir.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if "modules" in node.module.split("."):
                    raise AssertionError(
                        f"Architecture violation in {py_file}: "
                        f"shared module imports from modules: {node.module}"
                    )


if __name__ == "__main__":
    test_no_private_cross_module_imports()
    test_shared_does_not_import_modules()
    print("architecture tests OK")
