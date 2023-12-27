# Diary with ChatGPT Comment

## Overview
This project integrates ChatGPT with diary entries to provide AI-driven comments and insights on your personal reflections.

## Features
- **Diary Writing**: Save your thoughts in a digital diary.
- **AI Comments**: Get unique perspectives from ChatGPT on your diary entries.
- **Text Analysis**: Utilize tools for token counting and word frequency to explore your writing patterns.

## Prerequisites
- Python3
- OpenAI's GPT-3.5 (or newer) API key

## Setup
1. **Configure Environment**:
   - Install Python and set up your environment.
   - Obtain an OpenAI API key and store it as an environment variable named `OPENAI_API_KEY`.
   
2. **Clone Repository**:
   - Clone this repository to your local machine.

3. **Edit `config.py`**:
   - Open `config.py` file.
   - Edit the `diary_dir` variable to set your diary storage directory.
   - Edit the `text_app` variable to set your default writing tool of your diary.
   - Edit the `model` variable to specify which branch of large language model to use.

4. **Edit `sys_prompt.txt` and diary_prompt.txt**
   - `sys_prompt.txt` stores the message which will be shown in the very first line of the request, to give ChatGPT a background of you.
   - `diary_prompt.txt` stores the message which will be shown just before the your last diary in the request, to tell ChatGPT that they should comment only the last diary.

5. **Pin Shortcut (Opitonal)**:
   - For ease of access, pin the shortcut of the script to your start page or your desktop.

## Usage
1. **Writing Diary**:
   - Run `create_diary.py` to write and save entries in your chosen directory.

2. **Generating Comments**:
   - Edit the `system_prompt` in `create_comment.py` to customize ChatGPT's interaction with your diary entries.

3. **Analyzing Entries (Optional)**:
   - Use `count_token.py` and `word_frequency.py` to analyze the length and common themes of your entries.

