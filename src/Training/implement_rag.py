import json
import os
from pydoc import cli
from aiohttp import Payload
from dotenv import load_dotenv
from openai import OpenAI
import requests
import ollama

load_dotenv()
def process_jsonl(file_path, model="mistralai/Mistral-Small-24B-Instruct-2501"):
    # Get API key from .env file
    api_key = os.getenv('DEEPINFRA_API_KEY')
    if not api_key:
        raise ValueError("DEEPINFRA_API_KEY not found in .env file")
        
    client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepinfra.com/v1/openai"
        )
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
                data = json.loads(line)
                print(data)
                
                # Skip empty entries
                if not data["text"].strip():
                    continue
                
                # Customize your prompt here
                payload = client.chat.completions.create(
                    model=model,
                    messages={"role": "system", "content": f"Summarize this webpage content in 2 sentences:\n\n{data["text"]}"},
                    stream=False,
                    temperature=0.7,
                    max_tokens=8_000
                )
                summary = payload.choices[0].message.content


                
                print(f"\n--- Entry {line_num} ---")
                print(f"URL: {data["metadata"]["url"]}")
                print(f"Summary: {summary}")
                
                # Optional: save results
                output = {
                    "url": f"URL: {data["metadata"]["url"]}",
                    "original_text": data["text"] + "...",
                    "model_output": summary
                }
                
                with open('output.jsonl', 'a') as out:
                    out.write(json.dumps(output) + '\n')
                    
            # except Exception as e:
            #     print(f"Error on line {line_num}: {e}")

# Run it
process_jsonl('IC_data.jsonl')
