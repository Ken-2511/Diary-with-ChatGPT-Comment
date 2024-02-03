# this program is used to make comments in my diary
# when run, it first goes through the directory to see if there is a file newly created
# then request for chatGPT to add a comment

import os
import json
import math
import time
import count_token
from openai import OpenAI
from config import diary_dir, model
import jieba
import unicodedata

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
sys_prompt_dir = "sys_prompt.txt"
diary_prompt_dir = "diary_prompt.txt"
current_diary_dir = ""
need_comment = True

# 解释一下token_limit这个变量：
# 每一次发送请求GPT给评价的时候，这个程序都会加载之前的一部分日记，好让GPT有上下文，能看懂当前的日记写的是什么。
# 但是因为GPT一次性能看的消息的长度是有限的，比如GPT-4限制8192token。
# 不过最近openai更新了，有一个叫gpt-4-1106-preview的模型支持128000token的输入，这意味着我们可以一次性把所有内容都丢给它。
# 当然，因为这个是计费的，尽管不贵，但是如果每次都把所有日记丢给它，并且每天都请求评论的话，性价比可能就有点低了
# 所以这个变量的意义就是限制GPT能看到的先前日记和当前日记的总量。

# ENGLISH VERSION
# Explain the variable `token_limit`
# each time we request ChatGPT to comment, this program loads some of the previous diaries, to make ChatGPT has a context of what we the diary is talking about.
# For example, the newest diary may contain some people's name or some event that happened several days ago.
# ChatGPT will get a better understand of what the author is talking about.
# Since ChatGPT has a "context window". GPT-3.5 has a context window of 4096 tokens, and GPT-4 has a context window 8192 tokens.
# The total tokens of our request cannot exceed this limit. So we define `token limit` to make sure that it is within the limit.
# Although the newest model `gpt-4-1106-preview` has a 128,000 tokens context window, it is too expensive to let them see all the diaries at once.
token_limit = 7200


def make_comment(messages):
    """request ChatGPT to add a comment to my diary,
    and generate a comment file"""
    # request
    response = client.chat.completions.create(model=model, messages=messages)
    content = response.choices[0].message.content
    # save the comment
    with open(os.path.join(current_diary_dir, "comment.txt"), "w", encoding="utf-8") as file:
        file.write(content)


def diary_sort_key(dir_name):
    """Helper function. after loading the diaries, sort them"""
    nums = dir_name.split('-')
    return [int(n) for n in nums]


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


def get_relativity_score(text1: str, text2: str, length: int, index: int):
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

    same_word_score = 1
    text1_words = list(jieba.cut(text1))
    filter_meaningless_words(text1_words)
    for word in text1_words:
        same_word_score += text2.count(word)
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
    for i in range(1, length-2):
        score = get_relativity_score(text1, messages[i]["content"], length, i)
        rela_scores.append(score)
    # if num_tokens exceeds 7200, then clip, else don't clip
    while count_token.num_tokens_from_messages(messages, model) > token_limit:
        # the first one is system prompt
        # the second last is system prompt
        # the last one is needed diary
        choice = rela_scores.index(min(rela_scores))
        rela_scores.pop(choice)
        messages.pop(choice+1)


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
    diary_dirs = os.listdir(diary_dir)
    # remove the files which does not follow the format `yyyy-mm-dd-hh-mm-ss`
    diary_dirs = [dir_name for dir_name in diary_dirs if len(dir_name.split('-')) == 6]
    diary_dirs.sort(key=diary_sort_key, reverse=False)
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
        make_comment(messages)
        t1 = time.time()
        print(f"Comment added. Time cost: {int(t1 - t0)} sec. Please check it in `{diary_dir}`.")
    else:
        print("No comment has been added.")
input("Press enter to continue...")
