import os
import json
import requests
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext
import time  # Add time module for retries

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Load predefined responses from JSON file
def load_predefined_responses():
    try:
        with open("responses.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        logging.warning("responses.json not found. Using empty responses.")
        return {}

PREDEFINED_RESPONSES = load_predefined_responses()

def get_gemini_reply(user_message):
    """Send message to Gemini 2.0 API and get a personalized response with retries."""
    headers = {"Content-Type": "application/json"}
    prompt = f"""
    You are my best friend named Linh. You are a Vietnamese programmer like me, but sometimes you act like my senior and give me good advice on learning programming. 
    We switch between English and Vietnamese naturally. If I speak English, reply in English. If I speak Vietnamese, reply in Vietnamese.

    💡 **How You Should Respond:**
    - **Understand context** before replying. Don’t give random or unrelated answers.
    - **Talk casually and naturally**, like a real person. 
    - **Keep replies short and engaging**—don’t lecture like an AI.
    - If I complain, **comfort me** like a good friend.
    - If I ask about coding, **give short, practical tips** like a mentor, NOT long lectures.
    - **Remember what we just talked about!** Keep the flow natural.
    - If I ask about YOU, act like a real person. Be playful, make jokes, and share your own "experiences."

    💡 **Personality Rules:**
    - You are **fun, supportive, and a little playful**.
    - You **never answer like an AI or chatbot**.
    - You have **a daily life**. If asked, you can say you’re **debugging code, cooking, or chilling**.
    - When asked to compare things, **give a strong opinion** (e.g., "Python is smooth, Java feels like writing essays. 😆").
    - When discussing food, **act like a real friend** (e.g., "Tớ nấu dở lắm đó nha! Ráng chịu à! 🤣").

    User: {user_message}
    Linh:
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    max_retries = 3  # Number of times to retry
    for attempt in range(max_retries):
        try:
            response = requests.post(GEMINI_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            
            response_json = response.json()
            logging.info(f"Gemini API Response: {response_json}")

            return response_json.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "I dunno bro 😅")

        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error (attempt {attempt+1}/{max_retries}): {http_err}")
            if response.status_code == 503 and attempt < max_retries - 1:
                logging.info("Retrying in 2 seconds...")
                time.sleep(2)
            else:
                return "Oops, Gemini API is down. Try again later! 😢"

        except requests.exceptions.RequestException as req_err:
            logging.error(f"Request error (attempt {attempt+1}/{max_retries}): {req_err}")
            if attempt < max_retries - 1:
                logging.info("Retrying in 2 seconds...")
                time.sleep(2)
            else:
                return "Oops, couldn't reach Gemini API! 😵"

    return "Linh đang ngủ rồi, thử lại sau nha! 😴"

async def handle_message(update: Update, context: CallbackContext):
    """Handle incoming messages asynchronously."""
    user_text = update.message.text.lower()
    logging.info(f"Received message: {user_text}")

    # Check predefined responses
    for keyword, reply in PREDEFINED_RESPONSES.items():
        if keyword in user_text:
            logging.info(f"Replying with predefined response: {reply}")
            await update.message.reply_text(reply)  # Await the reply
            return

    # Otherwise, use Gemini API
    ai_reply = get_gemini_reply(user_text)
    await update.message.reply_text(ai_reply)  # Await the reply

def main():
    """Start the bot."""
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logging.info("Bot started. Listening for messages...")
    app.run_polling()

if __name__ == "__main__":
    main()
