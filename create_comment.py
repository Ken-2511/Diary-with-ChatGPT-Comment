# this program is used to make comments in my diary
# when run, it first goes through the directory to see if there is a file newly created
# then request for chatGPT to add a comment

import openai
import os
import win32api
import win32con
import json
import count_token
import math

openai.api_key = os.environ.get("OPENAI_API_KEY")
sys_prompt_dir = "sys_prompt.txt"
diary_prompt_dir = "diary_prompt.txt"
diary_dir = r"The\directory\of\your\diaries"
current_diary_dir = ""
need_comment = True
model = "gpt-4-1106-preview"
# 解释一下token_limit这个变量：
# 每一次发送请求GPT给评价的时候，这个程序都会加载之前的一部分日记，好让GPT有上下文，能看懂当前的日记写的是什么。
# 但是因为GPT一次性能看的消息的长度是有限的，比如GPT-4限制8192token。
# 不过最近openai更新了，有一个叫gpt-4-1106-preview的模型支持128000token的输入，这意味着我们可以一次性把所有内容都丢给它。
# 当然，因为这个是计费的，尽管不贵，但是如果每次都把所有日记丢给它，并且每天都请求评论的话，性价比可能就有点低了
# 所以这个变量的意义就是限制GPT能看到的先前日记和当前日记的总量。
token_limit = 8000


def make_comment(messages):
    """request ChatGPT to add a comment to my diary,
    and generate a comment file"""
    # request
    response = openai.ChatCompletion.create(model=model, messages=messages)
    content = response["choices"][0]["message"]["content"]
    # save the comment
    with open(os.path.join(current_diary_dir, "comment.txt"), "w", encoding="utf-8") as file:
        file.write(content)
    # save the log
    with open(os.path.join(current_diary_dir, "log.txt"), "w", encoding="utf-8") as file:
        json.dump(response, file)


def diary_sort_key(dir_name):
    nums = dir_name.split('-')
    return [int(n) for n in nums]


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
    for i in range(len(text1)-1):
        word = text1[i:i+2]
        same_word_score += text2.count(word)
    same_word_score = 2 * math.log(same_word_score)
    len_score = -0.7 * math.log(len(text2))
    index_score = -1 * math.log(length - index)
    return same_word_score + len_score + index_score


def clip_messages(messages):
    """since the chatGPT has a maximum token limit,
    we have to clip the messages to ensure that it is within 32k tokens
    the language model should require 700 ~ 1000 tokens free for generating full response
    so the limits is 8192-1000=7200"""
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
        return f"（{y}年{mon}月{d}日{h}时{m}分{s}秒）"
    # load the system prompt
    with open(sys_prompt_dir, "r", encoding="utf-8") as file:
        content = file.read()
    sys_prompt = [{"role": "system", "content": content}]
    # load the diaries
    diary_dirs = os.listdir(diary_dir)
    diary_dirs.sort(key=diary_sort_key, reverse=False)
    # load the time_strs
    diaries = []
    for dir_name in diary_dirs:
        # for each dir, read the diary
        # if there is no `comment.txt` in a dir, then break and request for comment
        diary_name = os.path.join(diary_dir, dir_name, "diary.txt")  # load diary
        with open(diary_name, "r", encoding="utf-8") as file:
            content = get_time_str(dir_name)
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
            file.write("\n\n")
    return messages


if __name__ == '__main__':
    print("loading messages...")
    messages = load_messages()
    print(f"num_tokens={count_token.num_tokens_from_messages(messages, model)}, model={model}")
    if need_comment:
        print("requesting for the response...")
        make_comment(messages)
        win32api.MessageBox(0, "Comment added.", "create comment", win32con.MB_OK)
    else:
        win32api.MessageBox(0, "No comment has been added.", "create comment", win32con.MB_OK)
