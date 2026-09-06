import importlib
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import call, patch


class RebuildAllTests(unittest.TestCase):
    def import_module(self):
        return importlib.import_module("rebuild_all")

    def test_import_does_not_start_external_commands(self):
        sys.modules.pop("rebuild_all", None)
        with patch("subprocess.run") as run:
            self.import_module()
        run.assert_not_called()

    def test_run_command_uses_argument_list_without_shell(self):
        module = self.import_module()
        completed = subprocess.CompletedProcess(
            args=["tool", "argument with spaces"],
            returncode=0,
            stdout="ok\n",
            stderr="",
        )

        with patch.object(module.subprocess, "run", return_value=completed) as run:
            self.assertTrue(module.run_command(["tool", "argument with spaces"], "测试"))

        args, kwargs = run.call_args
        self.assertEqual(args[0], ["tool", "argument with spaces"])
        self.assertIs(kwargs["shell"], False)
        self.assertEqual(kwargs["env"]["PYTHONIOENCODING"], "utf-8")

    def test_python_script_path_with_spaces_stays_one_argument(self):
        module = self.import_module()
        script = Path("folder with spaces") / "script.py"

        with patch.object(module, "run_command", return_value=True) as run:
            self.assertTrue(
                module.run_python_script(
                    script,
                    "测试脚本",
                    "--name",
                    "value with spaces",
                )
            )

        run.assert_called_once_with(
            [sys.executable, os.fspath(script), "--name", "value with spaces"],
            "测试脚本",
        )

    def test_main_runs_all_steps_as_argument_lists(self):
        module = self.import_module()

        with patch.object(module, "run_command", return_value=True) as run:
            self.assertEqual(module.main(), 0)

        scripts = module.config.ROOT_DIR / "scripts"
        self.assertEqual(
            run.call_args_list,
            [
                call(["ollama", "list"], "步骤0：检查模型"),
                call(
                    [sys.executable, os.fspath(scripts / "pdf_to_book_txt.py")],
                    "步骤1：提取教材文本",
                ),
                call(
                    [sys.executable, os.fspath(scripts / "build_library.py"), "--llm-summaries"],
                    "步骤2：构建并验证结构化教材库",
                ),
            ],
        )


if __name__ == "__main__":
    unittest.main()
