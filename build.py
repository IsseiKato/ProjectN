"""
ビルドスクリプト: python build.py

dist/task-manager  (Linux/Mac) または dist/task-manager.exe (Windows) が生成される。
"""
import subprocess
import sys

subprocess.run(
    [sys.executable, "-m", "PyInstaller", "--clean", "task_manager.spec"],
    check=True,
)
print("\nビルド完了: dist/task-manager")
