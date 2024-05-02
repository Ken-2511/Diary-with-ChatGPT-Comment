import os
import config

word_len = 5


def load_all_diaries():
    diary_dir = config.diary_dir
    all_content = ""
    for folder_name in os.listdir(diary_dir):
        if folder_name.startswith("."):
            continue
        file_name = os.path.join(diary_dir, folder_name, "diary.txt")
        with open(file_name, "r", encoding="utf-8") as file:
            content = file.read()
            all_content += content
    return all_content


def count_frequency(all_diaries: str):
    all_words = dict()
    for i in range(len(all_diaries)-word_len+1):
        word = all_diaries[i:i+word_len]
        if all_words.get(word) is None:
            all_words[word] = 0
        all_words[word] += 1
    # convert the dictionary to list
    ans = list(all_words)
    for i in range(len(ans)):
        ans[i] = ans[i], all_words[ans[i]]
    ans.sort(key=lambda a: a[1], reverse=True)
    return ans


if __name__ == '__main__':
    all_diaries = load_all_diaries()
    frequency = count_frequency(all_diaries)
    for word, freq in frequency[:30]:
        print(word, freq)
