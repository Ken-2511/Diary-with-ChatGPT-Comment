import os

# check whether it is windows or linux
if os.name == 'nt':
    is_windows = True
else:
    is_windows = False

if is_windows:
    diary_dir = r"C:\Users\IWMAI\OneDrive\Personal-Diaries"
    text_app = "notepad"
    model = "gpt-4o"
else:
    diary_dir = "/home/iwmain/Documents/diaries"
    text_app = "mousepad"
    model = "gpt-4o"


# 解释一下token_limit这个变量：
# 每一次发送请求GPT给评价的时候，这个程序都会加载之前的一部分日记，好让GPT有上下文，能看懂当前的日记写的是什么。
# 但是因为GPT一次性能看的消息的长度是有限的，比如GPT-4限制8192token。
# 不过最近openai更新了，有一个叫gpt-4-1106-preview的模型支持128000token的输入，这意味着我们可以一次性把所有内容都丢给它。
# 当然，因为这个是计费的，尽管不贵，但是如果每次都把所有日记丢给它，并且每天都请求评论的话，性价比可能就有点低了
# 所以这个变量的意义就是限制GPT能看到的先前日记和当前日记的总量。

# ENGLISH VERSION
# Explain the variable `token_limit`:
# each time we request ChatGPT to comment, this program loads some of the previous diaries, to make ChatGPT has a context of what we the diary is talking about.
# For example, the newest diary may contain some people's name or some event that happened several days ago.
# ChatGPT will get a better understand of what the author is talking about.
# Since ChatGPT has a "context window". GPT-3.5 has a context window of 4096 tokens, and GPT-4 has a context window 8192 tokens.
# The total tokens of our request cannot exceed this limit. So we define `token limit` to make sure that it is within the limit.
# Although the newest model `gpt-4-1106-preview` has a 128,000 tokens context window, it is too expensive to let them see all the diaries at once.
token_limit = 8000


if __name__ == '__main__':
    print(diary_dir, text_app, model)
