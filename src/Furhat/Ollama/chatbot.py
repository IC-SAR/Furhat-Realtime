import ollama
from . import config 

def check_for_model(model: str):
  response = ollama.list()
  installed_models = [m['model'] for m in response['models']]
  for installed in installed_models:
    if installed == model:
      return
    
  print(f"found no model with the name of: {model}. Pulling...")
  try:
    ollama.pull(model)
  except ollama.ResponseError as e:
    print(f"Failed to download model: {model}. Try connecting to the internet, or check the model name for typos")
    raise
    
client = ollama.Client()
messages: list[dict[str, str]] = []
current_model: str = config.DEFAULT_MODEL
check_for_model(current_model)

