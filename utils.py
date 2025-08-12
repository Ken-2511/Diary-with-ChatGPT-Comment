"""This file stores some useful functions that are used in multiple files."""

import os
import re
import jieba
import openai
from pyexpat.errors import messages

import config
import base64
import numpy as np


def dir_sort_key(dir_name):
    """sort the dir by the date"""
    nums = dir_name.split('-')
    return [int(n) for n in nums]


def load_all_dir_names(path):
    """load all the dir names in the path and sort them by the date"""
    dir_names = []
    for dir_name in os.listdir(path):
        if len(dir_name.split('-')) != 6:
            continue
        dir_names.append(dir_name)
        # stop at when the dir has no comment, mean that the last dir has no comment
        # actually there is a chance that the last dir has a comment
        # it is when all the diaries have comments
        if not check_comment(os.path.join(path, dir_name)):
            break
    dir_names.sort(key=dir_sort_key)
    return dir_names


def read_diary(dir_name):
    """read the diary in the dir"""
    with open(os.path.join(dir_name, "diary.txt"), "r", encoding="utf-8") as file:
        return file.read()


def read_comment(dir_name):
    """read the comment in the dir"""
    with open(os.path.join(dir_name, "comment.txt"), "r", encoding="utf-8") as file:
        return file.read()


def check_comment(dir_name):
    """check whether the comment exists"""
    return os.path.exists(os.path.join(dir_name, "comment.txt"))


def encrypt(text, key):
    """xor encrypt the text"""
    key = key.encode("utf-8")
    key_len = len(key)
    text = text.encode("utf-8")
    result = bytearray()
    for i in range(len(text)):
        result.append(text[i] ^ key[i % key_len])
    return base64.b64encode(result).decode("utf-8")


def decrypt(text, key):
    """xor decrypt the text"""
    key = key.encode("utf-8")
    key_len = len(key)
    text = base64.b64decode(text.encode("utf-8"))
    result = bytearray()
    for i in range(len(text)):
        result.append(text[i] ^ key[i % key_len])
    return result.decode("utf-8")


def process_secrets(text, mode):
    # use regex to match the secrets
    pattern = r'<secret>(.*?)</secret>'
    with open("encrypt_key", "r", encoding="utf-8") as file:
        key = file.read()
    
    def repl(match):
        if mode == "encrypt":
            return f"<secret>{encrypt(match.group(1), key)}</secret>"
        elif mode == "decrypt":
            return f"<secret>{decrypt(match.group(1), key)}</secret>"
        else:
            raise ValueError(f"mode {mode} is not supported")
    return re.sub(pattern, repl, text, flags=re.DOTALL)


def _get_embedded_vector(text):
    client = openai.Client(api_key=config.api_key)
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-large"
    )
    vec = response.data[0].embedding
    return np.array(vec, dtype=np.float32)


def save_embedded_vector_from_diary(dir_name):
    # read the diary, embed the text, and save the vector
    content = read_diary(dir_name)
    content = process_secrets(content, "decrypt")
    # if there is a title, then add the title to the content
    if os.path.exists(os.path.join(dir_name, "title.txt")):
        with open(os.path.join(dir_name, "title.txt"), "r", encoding="utf-8") as file:
            title = file.read()
        content = title + "\n" + content
    vec = _get_embedded_vector(content)
    np.save(os.path.join(dir_name, "vec.npy"), vec)
    return vec


def get_time_str(dir_name):
    y, mon, d, h, m, s = [int(i) for i in dir_name.split('-')]
    return f"(Date: {y}.{mon}.{d}, time: {h}:{m})"


def save_title_from_diary(dir_name, time_str):
    # read the diary, get the title, and save the title
    content = read_diary(dir_name)
    content = time_str + "\n\n" + content
    # intentionally do not decrypt the secrets
    # content = process_secrets(content, "decrypt")
    # get the title
    client = openai.Client(api_key=config.api_key)
    response = client.chat.completions.create(
        model=config.model,
        messages=[
            {
                "role": "system",
                "content": "Generate a title for the diary as plain text only. Do not add quotation marks or any additional text."
            },
            {
                "role": "user",
                "content": content
            }
        ]
    )
    title = response.choices[0].message.content
    with open(os.path.join(dir_name, "title.txt"), "w", encoding="utf-8") as file:
        file.write(title)
    return title


def get_distance(v1, v2):
    return np.linalg.norm(v1 - v2)


def update_all_vectors(path, force=False):
    for dir_name in load_all_dir_names(path):
        if os.path.exists(os.path.join(path, dir_name, "vec.npy")) and not force:
            continue
        save_embedded_vector_from_diary(os.path.join(path, dir_name))


def update_all_titles(path, force=False):
    for dir_name in load_all_dir_names(path):
        if os.path.exists(os.path.join(path, dir_name, "title.txt")) and not force:
            continue
        title = save_title_from_diary(os.path.join(path, dir_name), get_time_str(dir_name))
        print(f"Title of {dir_name}: {title}")


if __name__ == '__main__':
    # with open(r"C:\Users\IWMAI\OneDrive\Personal-Diaries\2024-06-24-16-31-00\diary.txt", "r", encoding="utf-8") as file:
    # with open(r"C:\Users\IWMAI\OneDrive\Personal-Diaries\2024-07-12-14-33-15\diary.txt", "r", encoding="utf-8") as file:
    #     content = file.read()
    # content = process_secrets(content, "encrypt")
    # with open(r"C:\Users\IWMAI\OneDrive\Personal-Diaries\2024-06-24-16-31-00\diary.txt", "w", encoding="utf-8") as file:
    # # with open(r"C:\Users\IWMAI\OneDrive\Personal-Diaries\2024-07-12-14-33-15\diary.txt", "w", encoding="utf-8") as file:
    #     file.write(content)
    # print(content)
    update_all_titles(config.diary_dir)
    update_all_vectors(config.diary_dir)