"""Launch the Furhat realtime UI and background robot loop."""

from __future__ import annotations

import asyncio
import logging
import threading

from . import bootstrap
from .Robot import robot
from .UI import ui
from .Web import server as web_server


logger = logging.getLogger(__name__)


def _start_loop(event_loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(event_loop)
    event_loop.run_forever()

def main() -> None:
    logger.info("Starting Furhat Realtime.")
    # Dedicated asyncio loop on a background thread.
    loop = asyncio.new_event_loop()
    robot.attach_loop(loop)
    loop_thread = threading.Thread(target=_start_loop, args=(loop,), daemon=True)
    loop_thread.start()

    # Create the UI and pass the asyncio loop so callbacks can schedule coroutines safely.
    root = ui.create_ui(loop=loop)

    # Start the web control server (for the exe and remote control).
    web_server.start_server(loop)

    # Run the robot runtime on the same background loop used by UI/web callbacks.
    setup_future = asyncio.run_coroutine_threadsafe(robot.setup(), loop)
    closing = False

    def _on_close() -> None:
        nonlocal closing
        if closing:
            return
        closing = True
        try:
            robot.disconnect(wait=True)
        except Exception:
            logger.exception("Robot shutdown failed.")
        try:
            setup_future.cancel()
        except Exception:
            logger.exception("Failed to cancel robot setup task.")
        if loop.is_running():
            loop.call_soon_threadsafe(loop.stop)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", _on_close)
    root.mainloop()
    if not closing:
        _on_close()
    if loop_thread.is_alive():
        loop_thread.join(timeout=1.0)


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
