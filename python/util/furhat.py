from furhat_realtime_api import AsyncFurhatClient, FurhatClient
import asyncio


class Furhat:
  def __init__(self, ip: str):
    self.ip = ip
    self.furhat_real = AsyncFurhatClient(ip)
    asyncio.run(self.start_conversation())
    print("furhat initialized")
    