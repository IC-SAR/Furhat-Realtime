from furhat_realtime_api import AsyncFurhatClient, FurhatClient
import logging
import asyncio
import furhat_realtime_api
import config


class Furhat:
  def __init__(self, ip: str):
    self.ip = ip
    self.furhat_real = AsyncFurhatClient(ip)
    asyncio.run(self.start_conversation())
    print("furhat initialized")
    
  async def start_conversation(self):
    self.furhat_real.connect()
    self.state: FurhatState = FurhatState.IDLE
    await self.furhat_real.request


  
  