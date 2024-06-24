# this program is for making comments in my diary
# when running, it first goes through the directory to see if there is a file newly created
# then request for chatGPT to add a comment

import os
import math
import time
import datetime
import count_token
from openai import OpenAI
from config import diary_dir, model, token_limit
import utils
import encryption

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
SYS_PROMPT_NAME = "sys_prompt.txt"
DIARY_PROMPT_NAME = "diary_prompt.txt"
CURRENT_DIARY_DIR = ""  # This is for saving comment files
need_comment = True


# noinspection PyTypeChecker
def get_same_word_score(words1: str, words2: str) -> float:
    # convert the words1 to list and convert the words2 to a dictionary
    words1 = [line.split() for line in words1.split('\n') if line]
    for word in words1:
        word[1] = int(word[1])
    words2 = [line.split() for line in words2.split('\n') if line]
    for word in words2:
        word[1] = int(word[1])
    words2 = dict(words2)
    # calculate the score
    same_word_score = 1
    for word, count in words1:
        if word in words2:
            same_word_score += count * words2[word]
    return same_word_score


def get_length_score(diary_dir: str):
    content = utils.read_diary(diary_dir)
    length = len(content) + 1
    return length


def get_date_score(last_diary_dir, current_diary_dir):
    last_date = [int(i) for i in last_diary_dir.split('-')]
    last_date = datetime.datetime(*last_date)
    current_date = [int(i) for i in current_diary_dir.split('-')]
    current_date = datetime.datetime(*current_date)
    delta_time = last_date - current_date
    days = delta_time.days + 1
    return days


def clip_messages(messages):
    """since the chatGPT has a maximum token limit,
    we have to clip the messages to ensure that it is within the context window.
    Also, we should leave a ~800 token free space for GPT to generate their comment."""
    # get the relativity scores
    scores = get_rela_scores(diary_dir)
    scores.sort(key=lambda x: x[1], reverse=True)
    # if num_tokens exceeds 7200, then clip, else don't clip
    while count_token.num_tokens_from_messages(messages, model) > token_limit:
        # the first one is system prompt
        # the second last is system prompt
        # the last one is needed diary
        choice = scores.pop(-1)
        dir_name, score = choice
        for m in messages:
            if m["date"] == dir_name:
                messages.remove(m)
                break
        else:
            assert False


def get_rela_scores(path) -> list:
    """get the relativity scores of the diaries in the path
    the last diary is the one to be compared with
    return type: [[dir_name, relativity_score], ...]"""
    utils.update_all_meaningful_words(diary_dir)
    diaries = utils.load_all_dir_names(path)
    last_diary = diaries.pop(-1)
    # load the last diary's words statistics
    with open(os.path.join(path, last_diary, "words.txt"), "r", encoding="utf-8") as file:
        last_diary_words = file.read()
    # start to calculate all the relativity scores
    rela_scores = []
    for diary in diaries:
        with open(os.path.join(path, diary, "words.txt"), "r", encoding="utf-8") as file:
            content_words = file.read()
        sw_score = 0.5 * get_same_word_score(content_words, last_diary_words)
        # noinspection PyTypeChecker
        l_score = -1 * math.pow(get_length_score(os.path.join(diary_dir, diary)), 0.5)
        d_score = -1 * math.pow(get_date_score(last_diary, diary), 0.8)
        total_score = sw_score + l_score + d_score
        rela_scores.append([diary, total_score])
    return rela_scores


def regulate_messages(messages):
    """make sure that each item in the `messages` contains only the keys of `role` and `content`"""
    for i, m in enumerate(messages):
        m = {"role": m["role"], "content": m["content"]}
        messages[i] = m


def get_time_str(dir_name):
    y, mon, d, h, m, s = [int(i) for i in dir_name.split('-')]
    return f"(Date: {y}.{mon}.{d}, time: {h}:{m})"


def load_messages():
    """firstly get the system prompt
    then go through the diary directory
    sort the directories in date
    and load the diaries and comments in the `messages`
    if there is a dir without comment, break"""
    # load the system prompt
    with open(SYS_PROMPT_NAME, "r", encoding="utf-8") as file:
        content = file.read()
    sys_prompt = [{"role": "system", "content": content, "date": "None"}]
    # load the sorted diaries
    print("loading diaries...")
    diary_dirs = utils.load_all_dir_names(diary_dir)
    # load the time_strs
    print("adding to messages...")
    diaries = []
    for dir_name in diary_dirs:
        # for each dir, read the diary
        # if there is no `comment.txt` in a dir, then break and request for comment
        diary_name = os.path.join(diary_dir, dir_name, "diary.txt")  # load diary
        content = get_time_str(dir_name) + "\n\n"
        content += utils.read_diary(os.path.join(diary_dir, dir_name))
        diaries.append({"role": "user", "content": content, "date": dir_name})
        if not utils.check_comment(os.path.join(diary_dir, dir_name)):
            global CURRENT_DIARY_DIR
            CURRENT_DIARY_DIR = os.path.join(diary_dir, dir_name)
            break
    else:
        global need_comment
        need_comment = False
    # load the diary prompt which we put it in the second last message
    with open(DIARY_PROMPT_NAME, "r", encoding="utf-8") as file:
        content = file.read()
    diary_prompt = [{"role": "system", "content": content}]
    # compose the system prompt and the diaries
    messages = sys_prompt + diaries[:-1] + diary_prompt + diaries[-1:]
    print("clipping messages...")
    clip_messages(messages)
    print("regulating messages...")
    regulate_messages(messages)
    # save the messages
    with open("messages.txt", "w", encoding="utf-8") as file:
        for message in messages:
            file.write(message["content"])
            file.write("\n\n\n")
    return messages


def request_comment(messages) -> str:
    """request ChatGPT to add a comment to my diary"""
    # request
    response = client.chat.completions.create(model=model, messages=messages)
    content = response.choices[0].message.content
    return content


def save_comment(comment: str):
    f_name = os.path.join(CURRENT_DIARY_DIR, "comment.txt")
    with open(f_name, "w", encoding="utf-8") as file:
        file.write(comment)


def encrypt_last_diary():
    """encrypt the last diary"""
    # get the path of the last diary
    diary_dir = utils.load_all_dir_names(diary_dir)[-1]
    diary_path = os.path.join(diary_dir, "diary.txt")
    # read the diary
    content = utils.read_diary(diary_path)
    # encrypt the diary
    encrypted_content = encryption.encrypt_secret_recursive(content)
    # save the encrypted diary
    with open(diary_path, "w", encoding="utf-8") as file:
        file.write(encrypted_content)


if __name__ == '__main__':
    print("encrypting the last diary...")
    encrypt_last_diary()
    print("loading messages...")
    t0 = time.time()
    messages = load_messages()
    t1 = time.time()
    print(f"Messages loaded. Time cost: {t1 - t0:.2f} sec.")
    print(f"num_tokens={count_token.num_tokens_from_messages(messages, model)}, model={model}")
    if need_comment:
        print("requesting for the response...")
        t0 = time.time()
        comment = request_comment(messages)
        save_comment(comment)
        t1 = time.time()
        print(f"Comment added. Time cost: {int(t1 - t0)} sec. Please check it in `{CURRENT_DIARY_DIR}`.")
    else:
        print("No comment has been added.")
    input("Press enter to continue...")
