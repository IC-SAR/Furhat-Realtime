import tkinter as tk
from tkinter import ttk
import asyncio
import threading

from Robot import robot

def create_ui(loop):
    root = tk.Tk()
    root.title("Furhat UI")

    # Create a frame for the buttons
    button_frame = ttk.Frame(root, padding="10")
    button_frame.grid(row=0, column=0, sticky="W")

    def on_button_press(event):
        print("Button pressed: Start listening")
        if loop:
            # Schedule the async start_listening on the provided asyncio loop
            asyncio.run_coroutine_threadsafe(robot.on_listen_activate(), loop)
        else:
            # Fallback: run a temporary event loop in a thread
            threading.Thread(target=lambda: asyncio.run(robot.on_listen_activate()), daemon=True).start()

    def on_button_release(event):
        print("Button released: Stop listening")
        # stop_listening() is synchronous in current implementation
        if loop:
            # Schedule the async start_listening on the provided asyncio loop
            asyncio.run_coroutine_threadsafe(robot.on_listen_deactivate(), loop)
        else:
            # Fallback: run a temporary event loop in a thread
            threading.Thread(target=lambda: asyncio.run(robot.on_listen_deactivate()), daemon=True).start()

    listen_button = ttk.Button(button_frame, text="Hold to Listen")
    listen_button.grid(row=0, column=0, padx=5, pady=5)
    listen_button.bind("<ButtonPress-1>", on_button_press)
    listen_button.bind("<ButtonRelease-1>", on_button_release)

    return root
