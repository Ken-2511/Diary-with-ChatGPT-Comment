# Diary with ChatGPT Comments

## Overview
This project integrates ChatGPT with your personal diary entries to provide AI-driven comments, insights, and analyses on your reflections. It helps you to better understand your thoughts by providing meaningful feedback and deeper perspectives through AI.

## Features
- **Diary Writing**: Easily save and organize your thoughts in a digital diary.
- **AI Comments**: Get personalized and insightful comments from ChatGPT based on the context of your recent diary entries.
- **Content Analysis**: Use built-in tools for token counting, word frequency analysis, and relativity scoring to explore patterns and themes in your writing.
- **Diary Encryption**: Secure your diary entries with encryption features.
- **Customizable AI Prompts**: Modify system prompts to tailor ChatGPT’s feedback to your preferences.

## Prerequisites
- Python 3.x
- OpenAI's GPT-4 (or newer) API key

## Setup
1. **Install Dependencies**:
   - Install the required packages by running:
     ```bash
     pip install -r requirements.txt
     ```
   - This should cover all required dependencies such as `numpy`, `openai`, `jieba`, etc.

2. **Configure Environment**:
   - Obtain an OpenAI API key from [OpenAI](https://beta.openai.com/signup/).
   - Store your API key as an environment variable named `OPENAI_API_KEY`.

3. **Clone Repository**:
   - Clone this repository to your local machine using:
     ```bash
     git clone https://github.com/yourusername/diary-with-chatgpt-comments.git
     ```

4. **Configure `config.py`**:
   - Open the `config.py` file.
   - Edit the `diary_dir` variable to specify the directory where your diary files will be stored.
   - Modify the `text_app` variable to set the default text editor for writing your diary.
   - Adjust the `model` variable to specify which GPT model to use (e.g., `gpt-4`).

5. **Customize Prompts**:
   - Edit `sys_prompt.txt` to provide the system message that will serve as a background introduction for ChatGPT when it reads your diary entries.
   - Customize `diary_prompt.txt` to guide ChatGPT on how to comment on your latest diary entry.

6. **Optional: Create Shortcuts**:
   - For easy access, you can create and pin a shortcut for the main script (`create_comment.py`) to your start menu or desktop.

## Usage
1. **Write a Diary Entry**:
   - To write a diary entry, simply add a text file in the `diary_dir` directory following the format `YYYY-MM-DD-HH-MM-SS.txt`.

2. **Generate AI Comments**:
   - Run `create_comment.py` after writing your diary to request a comment from ChatGPT based on your latest entry:
     ```bash
     python create_comment.py
     ```
   - The script will analyze your most recent diary and provide comments in the same directory.

3. **Encrypt Your Diary**:
   - To secure your diary entries, run the encryption function in `create_comment.py`:
     ```bash
     python create_comment.py
     ```
   - This will automatically encrypt the latest diary entry.

4. **Analyze Your Entries** (Optional):
   - Use the included tools for analyzing your diary contents:
     - **Token Counting**: Check how many tokens your diary entries use, helpful for managing ChatGPT's context window.
     - **Word Frequency Analysis**: Analyze common words and themes across your diary.
     - **Relativity Scoring**: Determine how similar your latest entry is to previous ones based on content and word frequency.

## Example Workflow
1. **Write a new diary entry** using your preferred text editor.
2. **Run the script** to get comments and feedback on your entry.
3. **View AI comments** in the same folder as your diary.
4. Optionally, **analyze or encrypt your diary** entries for additional insights and security.

## Future Improvements
- **More Advanced Commenting**: Implement more nuanced comment generation that takes into account emotional tone and historical patterns in your diary.
- **Enhanced Encryption**: Add additional layers of security to further protect diary entries.
- **Web Interface**: Build a simple web interface for easier diary writing and AI interaction.
