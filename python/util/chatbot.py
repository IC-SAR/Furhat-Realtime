from ast import Dict
from mimetypes import init
from typing import Generator
import ollama
import re

class ChatBot:
  def __init__(
      self,
      ):
    self.client = ollama.Client()
    self.messages: list[Dict[str, str]] = []

  def set_model(self, model: str):
    """
    Designed to be a builder function to set the model. 
    Will download a new model if it doesn't exist.

    :param model: Model name from ollama.
    :type model: str
    """
    response = ollama.list()
    installed_models = [m['model'] for m in response['models']]
    for installed in installed_models:
      if (installed == model): break
    else:
      print(f"found no model with the name of: {model}. Pulling...")
      ollama.pull(model)

    self.model: str = model
    return self

  def send_token(self, prompt: str) -> Generator[str, None, None]:
    """
    Gives every token in a generator from the current ollama model
    
    :param prompt: the message from the user
    :type prompt: str
    :return: Generator of every token
    :rtype: Generator[str, None, None]
    """
    self.messages.append({'role':'user', 'content':prompt})
    full_response: str = ""

    stream = self.client.chat(
      model=self.model,
      messages=self.messages,
      stream=True
    )
  
    for chunk in stream:
      if 'message' in chunk and 'content' in chunk['message']:
          token = chunk['message']['content']
          full_response += token
          yield token
    
    if full_response:
      self.messages.append({'role': 'assistant', 'content': full_response})

  def send_regex(self, prompt: str, regex: str) -> Generator[str, None, None]:
    """
    Modification of send_token(), to split up the generation into
    easier sections of text for furhat.
    
    :param prompt: the message from the user
    :type prompt: str
    :param regex: A regex to split send_token()
    :type regex: str
    :rtype: Generator[str, None. None]
    """
    buffer = ""
    for token in self.send_token(prompt):
      buffer += token
      match = re.search(regex, buffer)
      while match:
        end_index = match.end()
        sentence = buffer[:end_index]
        yield sentence
        buffer = buffer[end_index:]
        
        match = re.search(regex, buffer)

    if buffer:
      yield buffer

  def send_sentence(self, prompt: str) -> Generator[str, None, None]:
    """
    sends the response of a prompt in sentences instead of tokens. 
    Look at send_regex() for more detail & control.
    """
    return self.send_regex(prompt, r'(?<=[.!?])\s+')
    
if __name__ == "__main__":
  chat = ChatBot().set_model("gemma3:4b")

  for item in chat.send_sentence("Hello, world!"):
    print(item)
