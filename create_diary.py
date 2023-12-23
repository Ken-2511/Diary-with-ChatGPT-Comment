import os
from datetime import datetime

diary_dir = r"The\directory\of\your\diaries"

now = datetime.now()
dir_name = os.path.join(diary_dir, f"{now.year}-{now.month}-{now.day}-{now.hour}-{now.minute}-{now.second}")
os.mkdir(dir_name)
diary_name = os.path.join(dir_name, f"diary.txt")
with open(diary_name, "w", encoding="utf-8") as file:
    pass
os.system(f"notepad {diary_name}")
