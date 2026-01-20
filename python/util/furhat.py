import logging
from furhat_realtime_api import AsyncFurhatClient, FurhatClient
import asyncio


class Furhat:
  def __init__(self, ip: str):
    self.ip = ip
    self.furhat_real: FurhatClient = FurhatClient(ip)
    self.furhat_real.set_logging_level(logging.INFO)
    self.furhat_real.connect()