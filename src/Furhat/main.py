"""Launch the Furhat realtime UI and background robot loop."""

import asyncio
import threading

try:
    from .Robot import robot
    from .UI import ui
except ImportError:
    # Allow running as a script (python src/Furhat/main.py).
    from Robot import robot
    from UI import ui


def _start_loop(event_loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(event_loop)
    event_loop.run_forever()


def _start_robot() -> None:
    asyncio.run(robot.setup())


def main() -> None:
    # Dedicated asyncio loop on a background thread.
    loop = asyncio.new_event_loop()
    loop_thread = threading.Thread(target=_start_loop, args=(loop,), daemon=True)
    loop_thread.start()

    # Create the UI and pass the asyncio loop so callbacks can schedule coroutines safely.
    root = ui.create_ui(loop=loop)

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


if __name__ == "__main__":
    main()
