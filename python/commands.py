

from util.command import Command, Scheduler
from util.furhat import Furhat
from util.chatbot import ChatBot
import asyncio

class Idle(Command):
  def __init__(self, robot: Furhat, chatbot: ChatBot):
    self.robot: Furhat = robot
    self.chatbot: ChatBot = chatbot
    print("test")

  def is_finished(self):
    return len(self.robot.furhat_real.request_attend_user()) > 0
  
  def end(self, interrupted: bool):
    pass
    # if interrupted: return

    # self.scheduler.schedule(Listening(self.robot, self.chatbot, self.scheduler))

# class Listening(Command):
#   def __init__(self, robot: Furhat, chatbot: ChatBot, scheduler: Scheduler):
#     self.robot: Furhat = robot
#     self.chatbot: ChatBot = chatbot
#     self.scheduler: Scheduler = scheduler
#     self.speaker_sentence = ""
#     self.is_speaker_done = False

#   def is_finished(self):
#     return self.is_speaker_done
  
#   def execute(self):
#     self.speaker_sentence = self.robot.furhat_real.request_listen_start()
#     self.is_speaker_done = True

#   def end(self, interrupted: bool):
#     if interrupted: return

#     self.scheduler.schedule(Speaking(self.robot, self.chatbot))
    
  
class Response(Command):
  def __init__(self, robot: Furhat, chatbot: ChatBot):
    self.robot: Furhat = robot
    self.chatbot: ChatBot = chatbot
    self.speaker_sentence = ""
    self.is_speaker_done = False
    self.is_done_responding = False

  def is_finished(self):
    return self.is_done_responding
  
  def execute(self):
    print(self.speaker_sentence)
    if (not self.is_speaker_done):
      self.speaker_sentence = self.robot.furhat_real.request_listen_start()
      self.is_speaker_done = True
      
    elif (not self.is_done_responding):
      for item in self.chatbot.send_sentence(self.speaker_sentence):
        self.robot.furhat_real.request_speak_text(item)
      self.is_done_responding = True
        