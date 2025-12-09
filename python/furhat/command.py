class Command:
  def initialize(self):
    """Called when the command in scheduled."""
    pass

  def execute(self):
    """Called repeatedly while the command is running."""
    pass

  def is_finished(self) -> bool:
    """Returns True when the command should end"""
    return False
  
  def end(self, interrupted: bool):
    """Called once when the command ends or is interrupted"""
    pass

class Scheduler:
  def __init__(self):
    self.running_commands: list[Command] = []

  def schedule(self, command: Command):
    command.initialize()
    self.running_commands.append(command)
    print(f"Starting: {command}")

  def run(self):
    for command in self.running_commands[:]:
      command.execute()

      if command.is_finished():
        command.end(interrupted=False)
        self.running_commands.remove(command)
        print(f"Finished: {command}")