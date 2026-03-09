from __future__ import annotations

import concurrent.futures
import importlib
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


main_module = importlib.import_module("Furhat.main")


class MainShutdownTests(unittest.TestCase):
    def test_shutdown_timeout_logs_warning_and_forces_close(self) -> None:
        root = mock.Mock()
        loop = mock.Mock()
        robot_future = mock.Mock()
        robot_future.done.return_value = False
        disconnect_future = mock.Mock()
        disconnect_future.result.side_effect = concurrent.futures.TimeoutError()

        def _submit(coro: object, _loop: object) -> object:
            close = getattr(coro, "close", None)
            if callable(close):
                close()
            return disconnect_future

        with mock.patch.object(
            main_module.asyncio,
            "run_coroutine_threadsafe",
            side_effect=_submit,
        ), self.assertLogs(main_module.logger, level="WARNING") as logs:
            main_module._shutdown_runtime(root, loop, robot_future, timeout=0.01)

        self.assertTrue(any("timed out" in entry.lower() for entry in logs.output))
        disconnect_future.cancel.assert_called_once()
        robot_future.cancel.assert_called_once()
        loop.call_soon_threadsafe.assert_called_once_with(loop.stop)
        root.destroy.assert_called_once()


if __name__ == "__main__":
    unittest.main()
