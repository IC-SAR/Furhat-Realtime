import enum
from typing import Any, Coroutine
from furhat_realtime_api import AsyncFurhatClient, Events
from . import config
import asyncio
import logging
import Ollama


furhat = AsyncFurhatClient(config.IP) 
furhat.set_logging_level(logging.INFO)  
user_response: str = ""
partial_text = ""
recognized_text = ""


async def on_listen_activate():
  print("Listening...")
  await furhat.request_listen_start(
    partial=True, 
    concat=True,
    stop_no_speech=False, 
    stop_user_end=False,
    stop_robot_start=False
  )

async def on_listen_deactivate():
  print("Not Listening...")
  await furhat.request_listen_stop()
  global partial_text
  global recognized_text
  print("Heard: ", getattr(recognized_text, 'text', str(recognized_text)))
  say_text = Ollama.get_response_by_punctuation(getattr(recognized_text, 'text', str(recognized_text)))
  for word in say_text: print("Word: ", word); await furhat.request_speak_text(word, wait=True)
  partial_text = ""
  recognized_text = ""


async def on_partial(event):
  global partial_text

  partial_text = getattr(event, 'text', str(event))

async def on_hear_end(event):
  global recognized_text

  recognized_text = getattr(event, 'text', str(event))

def on_partial_speech(event):
  global user_response
  text_segment = getattr(event, 'text', str(event))
  print(text_segment)
  user_response += text_segment

async def on_speak_start(event):
  print("[speak start]", getattr(event, 'text', str(event)))

async def on_speak_end(event):
  print("[speak end]", getattr(event, 'text', str(event)))
  
async def setup():
  await furhat.connect()
  furhat.add_handler(Events.response_hear_partial, on_partial)
  furhat.add_handler(Events.response_hear_partial, on_hear_end)
  furhat.add_handler(Events.response_speak_start, on_speak_start)
  furhat.add_handler(Events.response_speak_end, on_speak_end)
  await furhat.request_speak_text("Activated", wait=True, abort=True)
  print("Activated")

  while True:
    await asyncio.sleep(1)

