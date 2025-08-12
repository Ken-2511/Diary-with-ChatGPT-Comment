# this program is for making comments in my diary
# when running, it first goes through the directory to see if there is a file newly created
# then request for chatGPT to add a comment

import os
import math
import time
import json
import datetime
import count_token
import numpy as np
from openai import OpenAI
from config import diary_dir, model, token_limit, api_key
import utils
from utils import check_comment
import re

client = OpenAI(api_key=api_key)
SYS_PROMPT_NAME = "sys_prompt.txt"
DIARY_PROMPT_NAME = "diary_prompt.txt"
CURRENT_DIARY_DIR = ""  # This is for saving comment files
need_comment = True
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_token_limit = input("Please input the token limit: ")
if _token_limit != "":
    token_limit = int(_token_limit)


def get_length_score(diary_dir):
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


def clip_diaries(diaries):
    """make the num of token of the diaries less than the token limit
    note that it is only the rough estimate, and the actual token num will be a little bit larger"""
    # sort the diaries by the relativity score
    diaries.sort(key=lambda x: x["relativity_score"], reverse=True)
    new_diaries = []
    for i in range(len(diaries)):
        new_diaries.append(diaries[i])
        if count_token.num_tokens_from_diaries(new_diaries) > token_limit:
            break
    # sort the diaries by the date
    new_diaries.sort(key=lambda x: utils.dir_sort_key(x["dir_name"]))
    return new_diaries


def get_content_rela_scores(path) -> tuple:
    """get the content and the relativity scores of the diaries in the path
    the last diary is the one to be compared with
    return type: ([{"dir_name": str,
                    "relativity_score": float,
                    "content": str}, ...],  <- all diaries
                    {"dir_name": str, "content": str})  <- last diary"""
    utils.update_all_titles(path)
    utils.update_all_vectors(path)
    # load diary names
    diary_names = utils.load_all_dir_names(path)
    diaries = [{"dir_name": dn} for dn in diary_names]
    # load diary contents
    for d in diaries:
        content = utils.read_diary(os.path.join(path, d["dir_name"]))
        content = utils.process_secrets(content, "decrypt")
        d["content"] = content
    # load the diary vectors
    for d in diaries:
        d["vector"] = np.load(os.path.join(path, d["dir_name"], "vec.npy"))
    # get the last diary
    last_diary = diaries.pop(-1)
    # start to calculate all the relativity scores
    for d in diaries:
        v_score = -20 * math.log2(utils.get_distance(last_diary["vector"], d["vector"] + 1e-9))
        l_score = -1 * math.pow(get_length_score(os.path.join(diary_dir, d["dir_name"])), 0.3)
        d_score = -1 * math.pow(get_date_score(last_diary["dir_name"], d["dir_name"]), 0.5)
        total_score = v_score + l_score + d_score
        d["relativity_score"] = total_score
    # get the time_strs
    for d in diaries:
        d["content"] = utils.get_time_str(d["dir_name"]) + "\n\n" + d["content"]
    last_diary["content"] = utils.get_time_str(last_diary["dir_name"]) + "\n\n" + last_diary["content"]

    return diaries, last_diary


def regulate_messages(messages):
    """make sure that each item in the `messages` contains only the keys of `role` and `content`"""
    for i, m in enumerate(messages):
        m = {"role": m["role"], "content": m["content"]}
        messages[i] = m


def load_messages():
    """firstly get the system prompt
    then go through the diary directory
    sort the directories in date
    and load the diaries and comments in the `messages`
    if there is a dir without comment, break"""
    # load the sorted diaries
    print("loading diaries...")
    diaries, last_diary = get_content_rela_scores(diary_dir)

    # clip the diaries
    diaries = clip_diaries(diaries)

    messages = []
    for diary in diaries:
        messages.append({"role": "user", "content": diary["content"]})

    # globals
    global CURRENT_DIARY_DIR
    CURRENT_DIARY_DIR = os.path.join(diary_dir, last_diary["dir_name"])

    # compose the system prompt and the diaries
    # load the system prompt
    with open(SYS_PROMPT_NAME, "r", encoding="utf-8") as file:
        content = file.read()
    sys_prompt = [{"role": "system", "content": content, "date": "None"}]
    # load the diary prompt
    with open(DIARY_PROMPT_NAME, "r", encoding="utf-8") as file:
        content = file.read()
    diary_prompt = [{"role": "system", "content": content}]
    # load the last diary
    last_diary_prompt = [{"role": "user", "content": last_diary["content"]}]
    messages = sys_prompt + messages + diary_prompt + last_diary_prompt

    # save the messages
    with open(os.path.join(PROJECT_ROOT, "messages.txt"), "w", encoding="utf-8") as file:
        # noinspection PyTypeChecker
        json.dump(messages, file, ensure_ascii=False, indent=4)
        # for message in messages:
        #     file.write(message["content"])
        #     file.write("\n\n\n")

    # if the last diary has a comment, then we don't need to request for a comment
    if check_comment(os.path.join(diary_dir, last_diary["dir_name"])):
        global need_comment
        need_comment = False

    return messages


def _is_reasoning_model(model_name: str) -> bool:
    name = (model_name or "").lower()
    return name.startswith("o") or ("reason" in name)


def _extract_tag_block(text: str, tag: str) -> str:
    pattern = re.compile(rf"<{tag}>([\s\S]*?)</{tag}>", re.IGNORECASE)
    match = pattern.search(text or "")
    return match.group(1).strip() if match else ""


def _save_thoughts(thoughts_text: str, context_header: str = ""):
    if not thoughts_text:
        return
    try:
        with open("thoughts.txt", "a", encoding="utf-8") as f:
            if context_header:
                f.write(context_header + "\n")
            f.write(thoughts_text.rstrip() + "\n\n")
    except Exception as e:
        print(f"Warning: failed to save thoughts.txt: {e}")


def request_comment(messages) -> str:
    """request ChatGPT to add a comment to my diary"""
    call_messages = list(messages)
    if _is_reasoning_model(model):
        call_messages = list(messages) + [
            {
                "role": "system",
                "content": (
                    "你是一个支持思考的模型。请在内部先进行详细推理，但不要在最终回答中暴露推理过程。\n"
                    "- 将你的完整思考过程输出在 <thoughts> 与 </thoughts> 标签中。\n"
                    "- 将最终给用户看的评论输出在 <final> 与 </final> 标签中。\n"
                    "- 最终回答只包含 <final> 部分的内容。"
                )
            }
        ]
    # request
    response = client.chat.completions.create(model=model, messages=call_messages)
    content = response.choices[0].message.content or ""

    if _is_reasoning_model(model):
        # Extract and persist thoughts; return only final
        thoughts = _extract_tag_block(content, "thoughts")
        final_text = _extract_tag_block(content, "final") or content
        header = f"[{datetime.datetime.now().isoformat()}] source={CURRENT_DIARY_DIR or 'unknown'} model={model}"
        _save_thoughts(thoughts, header)
        return final_text

    return content


def save_comment(comment: str):
    f_name = os.path.join(CURRENT_DIARY_DIR, "comment.txt")
    with open(f_name, "w", encoding="utf-8") as file:
        file.write(comment)


def encrypt_last_diary():
    """encrypt the last diary"""
    # get the path of the last diary
    diary_path = utils.load_all_dir_names(diary_dir)[-1]
    # if there is a comment, then do not encrypt the diary
    if check_comment(os.path.join(diary_dir, diary_path)):
        return
    diary_path = os.path.join(diary_dir, diary_path, "diary.txt")
    # read the diary
    with open(diary_path, "r", encoding="utf-8") as file:
        content = file.read()
    # encrypt the diary
    encrypted_content = utils.process_secrets(content, "encrypt")
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
    print(f"num_tokens={count_token.num_tokens_from_messages(messages)}, model={model}")
    if need_comment:
        print("requesting for the response...")
        t0 = time.time()
        comment = request_comment(messages)
        save_comment(comment)
        t1 = time.time()
        print(f"Comment added. Time cost: {t1 - t0:.2f} sec. Please check it in `{CURRENT_DIARY_DIR}`.")
    else:
        print("No comment has been added.")
    input("Press enter to continue...")
