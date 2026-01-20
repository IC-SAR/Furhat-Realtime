
from util.command import Command, Scheduler
from util.furhat import Furhat
from util.chatbot import ChatBot
from commands import Idle, Response

def main():
  furhat = Furhat("172.27.8.26")
  chatbot = ChatBot().set_model("gemma3:4b")

  scheduler = Scheduler()
  idle_command = Idle(furhat, chatbot)
  response_command = Response(furhat, chatbot)
  #listening_command = Listening(furhat, chatbot, scheduler)
  #speaking_command = Speaking(furhat, chatbot, scheduler)

  scheduler.schedule(idle_command)
  scheduler.schedule(response_command)
  while True:
    scheduler.run()

    if not scheduler.running_commands:
      break

  furhat.furhat_real.disconnect()

if __name__ == "__main__":
  main()
  