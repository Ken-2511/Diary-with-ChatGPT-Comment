print("starting to load diaries...")
import os
from config import diary_dir
import utils


def get_time_str(dir_name):
    y, mon, d, h, m, s = [int(i) for i in dir_name.split('-')]
    return f"(date: {y}.{mon}.{d}, time: {h}:{m})"


def load_all():
    diary_list = utils.load_all_dir_names(diary_dir)
    with open("all_diaries_and_comments.txt", "w", encoding="utf-8") as file:
        for dir_name in diary_list:
            print(f"loading {dir_name}")
            # for each dir, read the diary
            file.write(get_time_str(dir_name) + '\n')
            diary = utils.read_diary(os.path.join(diary_dir, dir_name))
            # diary = utils.remove_blank_lines(diary)
            file.write(diary + '\n\n')
            # read the comment
            if not os.path.exists(os.path.join(diary_dir, dir_name, "comment.txt")):
                continue
            comment = utils.read_comment(os.path.join(diary_dir, dir_name))
            # comment = utils.remove_blank_lines(comment)
            file.write(comment + '\n\n\n')


if __name__ == '__main__':
    # import time
    # start = time.time()
    load_all()
    # print(f"Time: {time.time()-start}s")
