import asyncio
import threading
from Ollama import chatbot, util
from Robot import robot, furhat
from UI import ui


# Start a dedicated asyncio event loop on a background thread
loop = asyncio.new_event_loop()

def _start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

# Clean shutdown: stop asyncio loop when window closes
def _on_close():
    robot.furhat.disconnect()
    loop.call_soon_threadsafe(loop.stop)
    root.destroy()
    
loop_thread = threading.Thread(target=_start_loop, args=(loop,), daemon=True)
loop_thread.start()

# Create the UI and pass the asyncio loop so UI callbacks can schedule coroutines safely
root = ui.create_ui(loop=loop)

# Run the blocking generator in a worker thread and schedule async speech on the asyncio loop
def background_worker(prompt: str):
    asyncio.run(robot.setup())

worker_thread = threading.Thread(
    target=background_worker,
    args=("hello, world. DO NOT USE EMOJIS IN YOUR RESPONSE",),
    daemon=True,
)
worker_thread.start()


root.protocol("WM_DELETE_WINDOW", _on_close)
root.mainloop()
furhat.disconnect()