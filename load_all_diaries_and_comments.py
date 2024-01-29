import os

diary_dir = "../diaries"


def diary_sort_key(dir_name):
    nums = dir_name.split('-')
    return [int(n) for n in nums]


def get_time_str(dir_name):
    y, mon, d, h, m, s = [int(i) for i in dir_name.split('-')]
    return f"(date: {y}.{mon}.{d}, time: {h}.{m})"


def remove_blank_lines(content: str):
    while True:
        index = content.find('\n\n')
        if index == -1:
            break
        content = content[:index] + content[index+1:]
    return content


def load_all():
    content = ""
    diary_list = os.listdir(diary_dir)
    diary_list.sort(key=diary_sort_key)
    for dir_name in diary_list:
        content += get_time_str(dir_name) + '\n'
        with open(os.path.join(diary_dir, dir_name, "diary.txt"), "r", encoding="utf-8") as file:
            content += remove_blank_lines(file.read())
        if not os.path.exists(os.path.join(diary_dir, dir_name, "comment.txt")):
            continue
        content += '\n\n'
        with open(os.path.join(diary_dir, dir_name, "comment.txt"), "r", encoding="utf-8") as file:
            content += remove_blank_lines(file.read())
        content += '\n\n'
    with open("all_diaries_and_comments.txt", "w", encoding="utf-8") as file:
        file.write(content)


if __name__ == '__main__':
    load_all()
