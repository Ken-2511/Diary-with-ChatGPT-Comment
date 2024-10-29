"""This file stores some useful functions that are used in multiple files."""

import os
import re
import jieba
import openai
from pyexpat.errors import messages

import config
import base64
import unicodedata
import numpy as np


def delete_dir(dir_path):
    """delete the dir and all the files in the dir recursively"""
    for file_name in os.listdir(dir_path):
        if os.path.isdir(os.path.join(dir_path, file_name)):
            delete_dir(os.path.join(dir_path, file_name))
        else:
            os.remove(os.path.join(dir_path, file_name))
    os.rmdir(dir_path)


def regulate_dir_name(path):
    """make the dir_name follow the format `yyyy-mm-dd-hh-mm-ss`
    use zero-fill"""
    for dir_name in os.listdir(path):
        if len(dir_name.split('-')) != 6:
            continue
        y, mon, d, h, m, s = [int(i) for i in dir_name.split('-')]
        new_name = f"{y:04d}-{mon:02d}-{d:02d}-{h:02d}-{m:02d}-{s:02d}"
        os.rename(os.path.join(path, dir_name), os.path.join(path, new_name))


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


def remove_blank_lines(content: str):
    """remove the blank lines in the content"""
    while True:
        index = content.find('\n\n')
        if index == -1:
            break
        content = content[:index] + content[index+1:]
    if content.endswith('\n'):
        content = content[:-1]
    return content


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


def parse_meaningful_words(content: str):
    """use jieba to parse words
    remove the stop words (aka functional words, meaningless words)
    return type: {word: count, ...}"""
    with open("meaningless_words.txt", "r", encoding="utf-8") as file:
        meaningless_words = file.read().split('\n')
    meaningful_words = dict()
    content = remove_blank_lines(content)
    for word in jieba.cut(content):
        # if the word is a stop word, then continue
        if word in meaningless_words:
            continue
        if word in ["\n", " ", "\t", "\r"]:
            continue
        if all(unicodedata.category(char).startswith('P') for char in word):
            continue
        if word.find(" ") != -1:
            continue
        # if the word is a meaningful word, then add it to the dictionary
        if meaningful_words.__contains__(word):
            meaningful_words[word] += 1
        else:
            meaningful_words[word] = 1
    return meaningful_words


def _stat_meaningful_words(dir_name):
    # deprecated
    """stat the meaningful words in the diary
    and save the result into a file"""
    content = read_diary(dir_name)
    words = parse_meaningful_words(content)
    # convert the dictionary to a list of tuples, and sort it by the count
    word_list = list(words.items())
    word_list.sort(key=lambda x: x[1], reverse=True)
    with open(os.path.join(dir_name, "words.txt"), "w", encoding="utf-8") as file:
        for word, count in word_list:
            word = word.lower()
            file.write(f"{word} {count}\n")


def _update_all_meaningful_words(path, force=False):
    # deprecated
    """update all the meaningful words in the diaries
    force means whether to update the diaries that have already been updated"""
    for dir_name in load_all_dir_names(path):
        if os.path.exists(os.path.join(path, dir_name, "words.txt")) and not force:
            continue
        _stat_meaningful_words(os.path.join(path, dir_name))


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


def save_title_from_diary(dir_name):
    # read the diary, get the title, and save the title
    content = read_diary(dir_name)
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
        title = save_title_from_diary(os.path.join(path, dir_name))
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
    update_all_titles(config.diary_dir, force=True)
    update_all_vectors(config.diary_dir, force=True)