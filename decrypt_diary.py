import utils
import os

diary_name = r"C:\Users\IWMAI\OneDrive\Personal-Diaries\2025-01-15-08-11-46\diary.txt"

with open(diary_name, "r", encoding="utf-8") as file:
	content = file.read()
	content = utils.process_secrets(content, "decrypt")
	print(content)