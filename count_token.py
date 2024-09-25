from idlelib.iomenu import encoding

import tiktoken
from config import model

encoding = tiktoken.encoding_for_model(model)


def num_tokens_from_list(messages: list):
    """Returns the number of tokens used by a list of messages."""
    num_tokens = 0
    for message in messages:
        num_tokens += num_tokens_from_text(message)
    return num_tokens

def num_tokens_from_diaries(diaries: list):
    """Returns the number of tokens used by a list of diaries."""
    num_tokens = 0
    for diary in diaries:
        num_tokens += num_tokens_from_text(diary["content"])
    return num_tokens

def num_tokens_from_text(text: str):
    """Returns the number of tokens used by a text."""
    return len(encoding.encode(text))

def num_tokens_from_messages(messages: list):
    """Returns the number of tokens used by a list of messages."""
    num_tokens = 0
    for message in messages:
        num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":  # if there's a name, the role is omitted
                num_tokens += -1  # role is always required and always 1 token

    num_tokens += 2  # every reply is primed with <im_start>assistant
    return num_tokens


if __name__ == '__main__':
    model = "gpt-3.5-turbo-0613"
    messages = [
        {"role": "system",
         "content": "You are a helpful, pattern-following assistant that translates corporate jargon into plain English."},
        {"role": "system", "name": "example_user", "content": "New synergies will help drive top-line growth."},
        {"role": "system", "name": "example_assistant", "content": "Things working well together will increase revenue."},
        {"role": "system", "name": "example_user",
         "content": "Let's circle back when we have more bandwidth to touch base on opportunities for increased leverage."},
        {"role": "system", "name": "example_assistant",
         "content": "Let's talk later when we're less busy about how to do better."},
        {"role": "user",
         "content": "This late pivot means we don't have time to boil the ocean for the client deliverable."},
    ]
    print(f"{num_tokens_from_messages(messages)} prompt tokens counted.")
    text = "This late pivot means we don't have time to boil the ocean for the client deliverable."
    print(f"{num_tokens_from_text(text)} tokens counted.")
    # Should show ~126 total_tokens
