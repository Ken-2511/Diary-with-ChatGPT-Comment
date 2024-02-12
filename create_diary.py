import os
from datetime import datetime
from config import *

now = datetime.now()
dir_name = os.path.join(diary_dir, f"{now.year:04d}-{now.month:02d}-{now.day:02d}-{now.hour:02d}-{now.minute:02d}-{now.second:02d}")
os.mkdir(dir_name)
diary_name = os.path.join(dir_name, f"diary.txt")
with open(diary_name, "w", encoding="utf-8") as file:
    pass
os.system(f"{text_app} {diary_name}")
