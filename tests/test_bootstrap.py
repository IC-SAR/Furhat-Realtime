from __future__ import annotations

import logging
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from Furhat import bootstrap  # noqa: E402


class BootstrapTests(unittest.TestCase):
    def test_source_log_dir_uses_build_logs(self) -> None:
        log_dir = bootstrap.get_runtime_log_dir()
        self.assertEqual(log_dir, ROOT / "build" / "logs")

    def test_configure_startup_logging_is_idempotent_for_same_path(self) -> None:
        root_logger = logging.getLogger()
        original_handlers = list(root_logger.handlers)

        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "app.log"
            try:
                first = bootstrap.configure_startup_logging(path=log_path)
                second = bootstrap.configure_startup_logging(path=log_path)

                self.assertEqual(first, log_path.resolve())
                self.assertEqual(second, log_path.resolve())

                matching_handlers = [
                    handler
                    for handler in root_logger.handlers
                    if isinstance(handler, logging.FileHandler)
                    and Path(handler.baseFilename).resolve() == log_path.resolve()
                ]
                self.assertEqual(len(matching_handlers), 1)
            finally:
                for handler in list(root_logger.handlers):
                    if handler not in original_handlers:
                        root_logger.removeHandler(handler)
                        try:
                            handler.close()
                        except Exception:
                            pass


if __name__ == "__main__":
    unittest.main()
