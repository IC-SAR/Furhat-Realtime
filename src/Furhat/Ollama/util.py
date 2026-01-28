import re
from typing import Generator

from ollama import chat

try:
    from . import chatbot
except ImportError:
    import chatbot

def get_full_response(prompt: str):
    chatbot.messages.append({"role": "user", "content": prompt})
    stream = chatbot.client.chat(
        model=chatbot.current_model,
        messages=chatbot.messages,
        stream=False,
        options={"temperature": chatbot.current_temperature},
    )
    print(stream.message.content)
    return stream.message.content



def get_response_by_token(prompt: str) -> Generator[str, None, None]:
    """
    Stream each token from the current Ollama model.

    :param prompt: the message from the user
    :type prompt: str
    :return: Generator of every token
    :rtype: Generator[str, None, None]
    """
    chatbot.messages.append({"role": "user", "content": prompt})
    full_response: str = ""
    stream = chatbot.client.chat(
        model=chatbot.current_model,
        messages=chatbot.messages,
        stream=True,
        options={"temperature": chatbot.current_temperature},
    )

    for chunk in stream:
        if "message" in chunk and "content" in chunk["message"]:
            token = chunk["message"]["content"]
            full_response += token
            yield token

    if full_response:
        chatbot.messages.append({"role": "assistant", "content": full_response})


def get_response_by_regex(prompt: str, regex: str) -> Generator[str, None, None]:
    """
    Modification of get_response_by_token(), to split up the generation into
    easier sections of text for furhat.
    
    :param prompt: the message from the user
    :type prompt: str
    :param regex: A regex to split send_token()
    :type regex: str
    :rtype: Generator[str, None. None]
    """

    buffer = ""
    for token in get_response_by_token(prompt):
        buffer += token
        match = re.search(regex, buffer)
        while match:
            end_index = match.end()
            sentence = buffer[:end_index]
            yield sentence
            buffer = buffer[end_index:]

            match = re.search(regex, buffer)

    if buffer:
        
        yield re.sub(r'[^a-zA-Z0-9]', '', buffer)



def get_response_by_punctuation(prompt: str) -> Generator[str, None, None]:
    return get_response_by_regex(prompt, r"(?<=[.!?])\s+")

if __name__ == "__main__":
    print("hi")
    t = get_response_by_punctuation("Hello, world!")
    for r in t:
        print(r, end="")
    
    t = get_response_by_punctuation("Say 10 sentences")
    for r in t:
        print(r, end="")