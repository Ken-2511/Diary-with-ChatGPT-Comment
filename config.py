import os

# check whether it is windows or linux
if os.name == 'nt':
    is_windows = True
else:
    is_windows = False

if is_windows:
    diary_dir = r"C:\Users\IWMAI\OneDrive\Personal-Diaries"
    text_app = "notepad"
    model = "gpt-4"
else:
    diary_dir = "/home/iwmain/Documents/diaries"
    text_app = "mousepad"
    model = "gpt-4"


if __name__ == '__main__':
    print(diary_dir, text_app, model)
