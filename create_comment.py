# this program is used to make comments in my diary
# when run, it first goes through the directory to see if there is a file newly created
# then request for chatGPT to add a comment

import os
import json
import math
import time
import count_token
from openai import OpenAI
from config import diary_dir, model, token_limit
import jieba
import unicodedata
import utils

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
sys_prompt_dir = "sys_prompt.txt"
diary_prompt_dir = "diary_prompt.txt"
current_diary_dir = ""
need_comment = True


def request_comment(messages) -> str:
    """request ChatGPT to add a comment to my diary"""
    # request
    response = client.chat.completions.create(model=model, messages=messages)
    content = response.choices[0].message.content
    return content


with open("meaningless_words.json", "r", encoding="utf-8") as file:
    meaningless_words = json.load(file)["words"]


def check_if_meaningless(word: str) -> bool:
    if word in meaningless_words:
        return True
    if word in ["\n", " ", "\t", "\r"]:
        return True
    if all(unicodedata.category(char).startswith('P') for char in word):
        return True
    return False


def filter_meaningless_words(word_list: list) -> None:
    for word in word_list:
        if check_if_meaningless(word):
            word_list.remove(word)


def get_relativity_score(words1: str, words2: str) -> float:
    """
    return the relativity between two texts.
    text1 is today's diary, and text2 is a diary before.
    length is the total length of the messages list
    index is the index of text2 in the messages list
    The rules are like this:
        with greater num of same words gets higher score
        with greater length gets lower score
        with smaller index gets lower score
    """
    # convert the words1 to list and convert the words2 to a dictionary
    words1 = [line.split() for line in words1.split('\n')]
    for word in words1:
        word[1] = int(word[1])
    words2 = [line.split() for line in words2.split('\n')]
    for word in words2:
        word[1] = int(word[1])
    words2 = dict(words2)
    # calculate the score
    for word, count in words1:
        if word in words2:
            same_word_score += count * words2[word]
    same_word_score = 2 * math.log(same_word_score)
    len_score = -0.7 * math.log(len(text2))
    index_score = -1 * math.log(length - index)
    return same_word_score + len_score + index_score


def clip_messages(messages):
    """since the chatGPT has a maximum token limit,
    we have to clip the messages to ensure that it is within the context window.
    Also, we should leave a ~800 token free space for GPT to generate their comment."""
    # get the relativity scores
    # rela_scores[i] == relativity score of messages[i-1]["content"]
    rela_scores = []
    text1 = messages[-1]["content"]
    length = len(messages)
    for i in range(1, length - 2):
        score = get_relativity_score(text1, messages[i]["content"], length, i)
        rela_scores.append(score)
    # if num_tokens exceeds 7200, then clip, else don't clip
    while count_token.num_tokens_from_messages(messages, model) > token_limit:
        # the first one is system prompt
        # the second last is system prompt
        # the last one is needed diary
        choice = rela_scores.index(min(rela_scores))
        rela_scores.pop(choice)
        messages.pop(choice + 1)


def get_rela_scores(path) -> list:
    """get the relativity scores of the diaries in the path
    the last diary is the one to be compared with
    return type: [[dir_name, relativity_score], ...]"""
    diaries = utils.load_all_dir_names(path)
    last_diary = diaries.pop(-1)
    # load the last diary's words statistics
    with open(os.path.join(path, last_diary, "words.txt"), "r", encoding="utf-8") as file:
        last_diary_words = file.read()
    
    rela_scores = []
    for diary in diaries:
        # load each diaries and calculate the score
        with open(os.path.join(path, diary, "words.txt"), "r", encoding="utf-8") as file:
            content_words = file.read()
        score = get_relativity_score(content_words, last_diary_words)
        rela_scores.append([diary, score])
    return rela_scores


def load_messages():
    """firstly get the system prompt
    then go through the diary directory
    sort the directories in date
    and load the diaries and comments in the `messages`
    if there is a dir without comment, break"""

    def get_time_str(dir_name):
        y, mon, d, h, m, s = [int(i) for i in dir_name.split('-')]
        return f"(Date: {y}.{mon}.{d}, time: {h}:{m})"

    # load the system prompt
    with open(sys_prompt_dir, "r", encoding="utf-8") as file:
        content = file.read()
    sys_prompt = [{"role": "system", "content": content}]
    # load the diaries
    diary_dirs = utils.load_all_dir_names(diary_dir)
    # load the time_strs
    diaries = []
    for dir_name in diary_dirs:
        # for each dir, read the diary
        # if there is no `comment.txt` in a dir, then break and request for comment
        diary_name = os.path.join(diary_dir, dir_name, "diary.txt")  # load diary
        with open(diary_name, "r", encoding="utf-8") as file:
            content = get_time_str(dir_name)
            content += "\n\n"
            content += file.read()
            diaries.append({"role": "user", "content": content})
        comment_name = os.path.join(diary_dir, dir_name, "comment.txt")  # load comment
        if not os.path.exists(comment_name):
            global current_diary_dir
            current_diary_dir = os.path.join(diary_dir, dir_name)
            break
    else:
        global need_comment
        need_comment = False
    # load the diary prompt which we put it in the second last message
    with open(diary_prompt_dir, "r", encoding="utf-8") as file:
        content = file.read()
    diary_prompt = [{"role": "system", "content": content}]
    # compose the system prompt and the diaries
    messages = sys_prompt + diaries[:-1] + diary_prompt + diaries[-1:]
    clip_messages(messages)
    # save the messages
    with open("messages.txt", "w", encoding="utf-8") as file:
        for message in messages:
            file.write(message["content"])
            file.write("\n\n\n")
    return messages


if __name__ == '__main__':
    print("loading messages...")
    messages = load_messages()
    print(f"num_tokens={count_token.num_tokens_from_messages(messages, model)}, model={model}")
    if need_comment:
        print("requesting for the response...")
        t0 = time.time()
        request_comment(messages)
        t1 = time.time()
        print(f"Comment added. Time cost: {int(t1 - t0)} sec. Please check it in `{diary_dir}`.")
    else:
        print("No comment has been added.")
input("Press enter to continue...")
