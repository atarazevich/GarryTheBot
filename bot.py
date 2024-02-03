import os
from dotenv import load_dotenv
import telebot
import tempfile
from openai import OpenAI
from pydub import AudioSegment
import requests
from pymongo import MongoClient
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TELEGRAM_API_KEY = os.getenv('TELEGRAM_API_KEY')

# Initialize Telebot and OpenAI
client = OpenAI()
bot = telebot.TeleBot(TELEGRAM_API_KEY)

# Initialize MongoDB connection
mongo_client = MongoClient(os.getenv('MONGODB_URI'))
db = mongo_client[os.getenv('MONGODB_NAME')]
chats_collection = db.chats

# In-memory storage for chat histories
chat_histories = {}

# Function to update chat history in both memory and MongoDB
def update_chat_history(chat_id, message):
    logger.info(f"Updating chat history for chat_id {chat_id}")
    # Add message to in-memory chat history
    if chat_id not in chat_histories:
        chat_histories[chat_id] = []
    chat_histories[chat_id].append(message)
    
    # Update chat history in MongoDB
    chats_collection.update_one(
        {'chat_id': chat_id},
        {'$push': {'messages': message}},
        upsert=True
    )

# Function to retrieve chat history from memory or MongoDB
def get_chat_history(chat_id):
    logger.info(f"Retrieving chat history for chat_id {chat_id}")
    if chat_id in chat_histories:
        return chat_histories[chat_id]
    else:
        # Try to pull from the database
        chat_record = chats_collection.find_one({'chat_id': chat_id})
        if chat_record:
            # If found in the database, update in-memory chat histories
            chat_histories[chat_id] = chat_record['messages']
            return chat_record['messages']
        else:
            # If not found, create a new record in the database and in-memory
            chats_collection.insert_one({'chat_id': chat_id, 'messages': []})
            chat_histories[chat_id] = []
            return chat_histories[chat_id]

@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
    logger.info(f"Handling /start or /help command from chat_id {message.chat.id}")
    bot.send_message(chat_id=message.chat.id, text="Hi! I'm a bot that can transcribe your voice messages and respond to you. Send me a voice message to get started!")

# Function to handle voice messages and interact with OpenAI's APIs
@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    chat_id = message.chat.id
    logger.info(f"Handling voice message from chat_id {chat_id}")
    try:
        # Retrieve the voice message file
        file_info = bot.get_file(message.voice.file_id)
        file = requests.get(f'https://api.telegram.org/file/bot{TELEGRAM_API_KEY}/{file_info.file_path}')

        # Save the file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.oga') as temp_voice:
            temp_voice.write(file.content)
            temp_voice_path = temp_voice.name

        # Convert the OGG file to WAV using pydub
        audio = AudioSegment.from_file(temp_voice_path, format="ogg")
        wav_temp_path = temp_voice_path.replace('.oga', '.mp3')
        audio.export(wav_temp_path, format='mp3')

        # Send the converted audio file to OpenAI for transcription
        with open(wav_temp_path, 'rb') as wav_file:
            transcription = client.audio.transcriptions.create(
                file=wav_file,
                model="whisper-1",
                response_format='text'
            )

        # Update chat history with the user's transcribed message
        update_chat_history(chat_id, {"role": "user", "content": transcription})
        chat_history = get_chat_history(chat_id)
        # Generate a chat completion using the transcription
        chat_response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=chat_history
        )

        # Extract the message to be converted to speech
        message_to_speak = chat_response.choices[0].message.content

        # Update chat history with the assistant's message
        update_chat_history(chat_id, {"role": "assistant", "content": message_to_speak})
        bot.send_message(chat_id=chat_id, text=message_to_speak)
        # Generate speech from the message and save to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_speech:
            speech_file_path = temp_speech.name

        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=message_to_speak
        )

        response.stream_to_file(speech_file_path)

        # Send the audio response back to the user
        with open(speech_file_path, 'rb') as speech_file:
            bot.send_voice(chat_id=chat_id, voice=speech_file)

        # Clean up the temporary file after sending the message
        os.unlink(speech_file_path)
        os.unlink(temp_voice_path)
        os.unlink(wav_temp_path)
        
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        bot.send_message(chat_id=chat_id, text="Sorry, an error occurred.")

@bot.message_handler(commands=['reset'])
def handle_reset(message):
    chat_id = message.chat.id
    logger.info(f"Resetting chat history for chat_id {chat_id}")

    # Reset the chat history in memory
    if chat_id in chat_histories:
        del chat_histories[chat_id]

    # Reset the chat history in MongoDB
    chats_collection.delete_one({'chat_id': chat_id})

    # Inform the user that the chat history has been reset
    bot.send_message(chat_id, "Your chat history has been reset.")

# Start the bot
logger.info("Starting bot polling")
bot.polling(none_stop=True)
