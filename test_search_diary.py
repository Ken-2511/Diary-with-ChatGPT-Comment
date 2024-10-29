# this file is a test for searching diary

import os
import numpy as np
from datetime import datetime
from config import *
from openai import OpenAI

client = OpenAI(api_key=api_key)


def get_embedding(text: str) -> np.ndarray:
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-large"
    )
    vec = response.data[0].embedding
    return np.array(vec, dtype=np.float32)


def sort_diaries_by_distance(vec: np.ndarray) -> list:
    distances = []
    for dir_name in os.listdir(diary_dir):
        vec_path = os.path.join(diary_dir, dir_name, "vec.npy")
        if not os.path.exists(vec_path):
            continue
        saved_vec = np.load(vec_path)
        distance = np.linalg.norm(vec - saved_vec)
        distances.append((dir_name, distance))
    distances.sort(key=lambda x: x[1])
    return distances


def sort_diaries_by_dot_product(vec: np.ndarray) -> list:
    dot_products = []
    for dir_name in os.listdir(diary_dir):
        vec_path = os.path.join(diary_dir, dir_name, "vec.npy")
        if not os.path.exists(vec_path):
            continue
        saved_vec = np.load(vec_path)
        dot_product = np.dot(vec, saved_vec)
        dot_products.append((dir_name, dot_product))
    dot_products.sort(key=lambda x: x[1], reverse=True)
    return dot_products


def print_first_n_diaries(n: int, distances: list):
    for i in range(n):
        dir_name, distance = distances[i]
        with open(os.path.join(diary_dir, dir_name, "diary.txt"), "r", encoding="utf-8") as file:
            diary = file.read()
        print(f"Diary {i + 1}:")
        print(f"Score: {distance}")
        print(diary)
        print()


if __name__ == '__main__':
    text = input("Enter the text: ")
    vec = get_embedding(text)
    # distances = sort_diaries_by_distance(vec)
    # print_first_n_diaries(5, distances)
    dot_products = sort_diaries_by_dot_product(vec)
    print_first_n_diaries(5, dot_products)