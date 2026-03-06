from __future__ import annotations

import asyncio
import threading

from .Robot import robot
from .UI import ui
from .Web import server as web_server


def _start_loop(event_loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(event_loop)
    event_loop.run_forever()


def _start_robot() -> None:
    asyncio.run(robot.setup())


def main() -> None:
    loop = asyncio.new_event_loop()
    loop_thread = threading.Thread(target=_start_loop, args=(loop,), daemon=True)
    loop_thread.start()

    root = ui.create_ui(loop=loop)
    web_server.start_server(loop)

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
