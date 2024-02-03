# GarryTheBot - Voice Transcription Bot

This repository contains the code for a Telegram bot that can transcribe voice messages and respond to users using OpenAI's APIs.

## Setup

### Environment Variables

Before running the bot, make sure to set up the following environment variables in a `.env` file:

```
TELEGRAM_API_KEY = '<your-telegram-api-key>'
MONGODB_URI = '<your-mongodb-uri>'
MONGODB_NAME = '<your-mongodb-name>'
```

### OpenAI API Key

To use OpenAI's APIs, you need to set up your OpenAI API key. Follow the steps below:

1. Open Terminal: You can find it in the Applications folder or search for it using Spotlight (Command + Space).
2. Edit Bash Profile: Use the command `nano ~/.bash_profile` or `nano ~/.zshrc` (for newer MacOS versions) to open the profile file in a text editor.
3. Add Environment Variable: In the editor, add the line below, replacing `your-api-key-here` with your actual API key:

   ```
   export OPENAI_API_KEY='your-api-key-here'
   ```

4. Save and Exit: Press `Ctrl+O` to write the changes, followed by `Ctrl+X` to close the editor.
5. Load Your Profile: Use the command `source ~/.bash_profile` or `source ~/.zshrc` to load the updated profile.
6. Verification: Verify the setup by typing `echo $OPENAI_API_KEY` in the terminal. It should display your API key.

### Python Dependencies

Install the required Python dependencies by running the following command:

```
pip install -r requirements.txt
```

## Usage

To start the bot, run the following command:

```
python bot.py
```

The bot will start polling for new messages and transcribe voice messages sent by users. It will respond with a text message and an audio response.

## License

This project is licensed under the [GNU GPLv3 License](https://choosealicense.com/licenses/gpl-3.0/).
