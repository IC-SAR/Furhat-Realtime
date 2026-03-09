"""Launch the Furhat realtime UI and background robot loop."""

import asyncio
import concurrent.futures
import logging
import threading

from . import bootstrap
from .Robot import robot
from .UI import ui
from .Web import server as web_server
from . import settings_store


logger = logging.getLogger(__name__)


def _start_loop(event_loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(event_loop)
    event_loop.run_forever()


def _shutdown_runtime(
    root: object,
    loop: asyncio.AbstractEventLoop,
    robot_future: concurrent.futures.Future[object],
    *,
    timeout: float = 5.0,
) -> None:
    disconnect_future: concurrent.futures.Future[object] | None = None
    try:
        disconnect_future = asyncio.run_coroutine_threadsafe(robot.disconnect_async(), loop)
        disconnect_future.result(timeout=timeout)
    except concurrent.futures.TimeoutError:
        logger.warning("Robot shutdown timed out; forcing close.")
        if disconnect_future is not None:
            disconnect_future.cancel()
    except Exception:
        logger.exception("Robot shutdown failed.")
    if not robot_future.done():
        robot_future.cancel()
    try:
        loop.call_soon_threadsafe(loop.stop)
    except RuntimeError:
        logger.warning("Event loop was already closed during shutdown.")
    root.destroy()


def main() -> None:
    logger.info("Starting Furhat Realtime.")
    settings = settings_store.load_settings()
    # Dedicated asyncio loop on a background thread.
    loop = asyncio.new_event_loop()
    loop_thread = threading.Thread(target=_start_loop, args=(loop,), daemon=True)
    loop_thread.start()

    # Create the UI and pass the asyncio loop so callbacks can schedule coroutines safely.
    root = ui.create_ui(loop=loop)

    # Start the web control server (for the exe and remote control).
    web_server.apply_settings(
        enabled=settings.web.enabled,
        port=settings.web.port,
        public_max_text_chars=settings.web.public_max_text_chars,
        public_cooldown_sec=settings.web.public_cooldown_sec,
    )
    web_server.start_server(loop, port=settings.web.port, enabled=settings.web.enabled)

    robot_future = asyncio.run_coroutine_threadsafe(robot.setup(), loop)

    def _on_close() -> None:
        _shutdown_runtime(root, loop, robot_future, timeout=5.0)

    root.protocol("WM_DELETE_WINDOW", _on_close)
    root.mainloop()
    if not robot_future.done():
        robot_future.cancel()


def run() -> int:
    log_path = bootstrap.configure_startup_logging()
    bootstrap.install_exception_logging()
    try:
        main()
    except Exception:
        logger.exception("Application startup failed.")
        bootstrap.show_startup_error(
            "Furhat Realtime failed to start.",
            log_path,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
