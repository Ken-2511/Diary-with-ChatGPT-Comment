import os
from config import diary_dir

def find_newest_file(root_folder):
    """
    Finds the newest file in a folder and its subfolders.

    Args:
    - root_folder (str): The path to the folder to search in.

    Returns:
    - str: The path to the newest file found.
    """
    newest_file = None
    newest_ctime = 0

    for foldername, subfolders, filenames in os.walk(root_folder):
        for filename in filenames:
            filepath = os.path.join(foldername, filename)
            ctime = os.path.getctime(filepath)
            if ctime > newest_ctime:
                newest_ctime = ctime
                newest_file = filepath

    return newest_file

# Example usage:
root_folder_path = diary_dir
print(find_newest_file(root_folder_path))
