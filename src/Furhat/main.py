"""Launch the Furhat realtime UI and background robot loop."""

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


def _start_robot() -> None:
    asyncio.run(robot.setup())


def main() -> None:
    logger.info("Starting Furhat Realtime.")
    # Dedicated asyncio loop on a background thread.
    loop = asyncio.new_event_loop()
    loop_thread = threading.Thread(target=_start_loop, args=(loop,), daemon=True)
    loop_thread.start()

    # Create the UI and pass the asyncio loop so callbacks can schedule coroutines safely.
    root = ui.create_ui(loop=loop)

    # Start the web control server (for the exe and remote control).
    web_server.start_server(loop)

    # Run the robot loop in a worker thread so the UI stays responsive.
    worker_thread = threading.Thread(target=_start_robot, daemon=True)
    worker_thread.start()

    def _on_close() -> None:
        robot.disconnect()
        loop.call_soon_threadsafe(loop.stop)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", _on_close)
    root.mainloop()
    robot.disconnect()


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
