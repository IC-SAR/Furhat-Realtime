import enum
from typing import Any, Coroutine
from furhat_realtime_api import AsyncFurhatClient, Events
from . import config
import asyncio
import logging


furhat = AsyncFurhatClient(config.IP) 
furhat.set_logging_level(logging.INFO)  
user_response: str = ""


async def on_listen_activate():
  print("Listening...")
  await furhat.request_listen_start(
    partial=True, 
    stop_no_speech=False, 
    stop_user_end=False
  )

async def on_listen_deactivate():
  print("Not Listening...")
  print(user_response)
  await furhat.request_listen_stop()
  furhat.request_speak_text(user_response, wait=True)
  user_response = ""

def on_partial_speech(event):
  global user_response
  text_segment = getattr(event, 'text', str(event))
  print(text_segment)
  user_response += text_segment
  
async def setup():
  await furhat.connect()
  furhat.add_handler(Events.response_hear_partial, on_partial_speech)
  await furhat.request_speak_text("Activated", wait=True)
  print("Activated")

  while True:
    await asyncio.sleep(1)

