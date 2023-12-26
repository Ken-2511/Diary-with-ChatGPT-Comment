# Diary with ChatGPT Comment

## Overview
This project integrates ChatGPT with diary entries to provide AI-driven comments and insights on your personal reflections.

## Features
- **Diary Writing**: Save your thoughts in a digital diary.
- **AI Comments**: Get unique perspectives from ChatGPT on your diary entries.
- **Text Analysis**: Utilize tools for token counting and word frequency to explore your writing patterns.

## Prerequisites
- Python
- OpenAI's GPT-3 (or newer) API key

## Setup
1. **Configure Environment**:
   - Install Python and set up your environment.
   - Obtain an OpenAI API key and store it as an environment variable named `OPENAI_API_KEY`.
   
2. **Clone Repository**:
   - Clone this repository to your local machine.

3. **Diary Folder Path**:
   - Configure the `diary_dir` variable in `create_diary.py` to set your diary storage directory.

4. **Pin Shortcut**:
   - For ease of access, pin the shortcut of the script to the start page on Windows.

## Usage
1. **Writing Diary**:
   - Run `create_diary.py` to write and save entries in your chosen directory.

2. **Generating Comments**:
   - Edit the `system_prompt` in `create_comment.py` to customize ChatGPT's interaction with your diary entries.

3. **Analyzing Entries**:
   - Use `count_token.py` and `word_frequency.py` to analyze the length and common themes of your entries.

## Contributing
Feel free to fork this repository and contribute by submitting pull requests.