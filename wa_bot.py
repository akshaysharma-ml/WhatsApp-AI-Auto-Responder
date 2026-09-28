"""
WhatsApp Human-Responder using OpenRouter (cloud AI)
Requires: pip install selenium webdriver-manager requests
Uses your free OpenRouter API key – no local AI needed.
"""

import time
import random
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ───────────────────────────────
# CONFIG – EDIT THIS
# ───────────────────────────────
OPENROUTER_API_KEY = "YOUR OPENROUTER API KEY "   # <-- PASTE YOUR KEY HERE
OPENROUTER_MODEL = "deepseek/deepseek-chat-v3-0324"  # free model (can change)
# Other free options:
#   "qwen/qwen-2.5-coder-32b-instruct"
#   "meta-llama/llama-3.3-70b-instruct"
# ───────────────────────────────

def generate_response(incoming_msg):
    """
    Calls OpenRouter free model to generate a natural, context-aware reply.
    """
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a friendly human WhatsApp user. "
                            "Reply casually, naturally, and concisely (1-2 sentences). "
                            "Use emojis occasionally. Never mention that you are an AI. "
                            "Always match the tone of the message."
                        )
                    },
                    {"role": "user", "content": incoming_msg},
                ],
                "temperature": 0.9,  # makes responses more varied
            },
            timeout=30,
        )
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"⚠️ OpenRouter error ({e}). Using fallback.")
        return random.choice([
            "Hmm, that's interesting! Tell me more.",
            "Oh really? How come?",
            "Haha, I see what you mean!",
            "Wait, that reminds me of something... anyway go on.",
            "I'm listening... what happened next?",
        ])

class WhatsAppResponder:
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 30)
        self.processed_messages = set()  # avoid replying twice to same message

    def login(self):
        """Open WhatsApp Web and wait for QR scan."""
        self.driver.get("https://web.whatsapp.com")
        print("⏳ Scan the QR code with your WhatsApp...")
        self.wait.until(EC.presence_of_element_located((By.XPATH, '//div[@data-testid="chat-list"]')))
        print("✅ Logged in!")

    def get_unread_chats(self):
        """Find chats with unread message badges."""
        try:
            return self.driver.find_elements(
                By.XPATH, '//div[@data-testid="chat-list"]//span[contains(@data-testid, "unread")]'
            )
        except:
            return []

    def open_chat(self, chat_element):
        """Click on a chat to open it."""
        chat_element.click()
        time.sleep(2)  # let messages load

    def get_latest_incoming_message(self):
        """Get the most recent incoming text in the open chat."""
        try:
            messages = self.driver.find_elements(
                By.XPATH, '//div[contains(@class, "message-in")]//span[contains(@dir,"auto")]'
            )
            return messages[-1].text.strip() if messages else None
        except:
            return None

    def send_message(self, text):
        """Type message with human-like character delays and send."""
        input_box = self.driver.find_element(By.XPATH, '//div[@data-testid="chat-input"]')
        input_box.click()
        time.sleep(random.uniform(0.5, 1.5))  # pause before typing

        # Type character by character (human speed)
        for char in text:
            input_box.send_keys(char)
            time.sleep(random.uniform(0.03, 0.08))

        # Pause before sending
        time.sleep(random.uniform(0.8, 1.8))
        input_box.send_keys("\ue007")  # Enter

    def run(self, check_interval=5):
        self.login()
        print("🤖 Replying to messages. Press Ctrl+C to stop.\n")

        while True:
            try:
                unread_chats = self.get_unread_chats()
                if unread_chats:
                    chat = unread_chats[0]
                    # Get chat name for log
                    chat_name = chat.find_element(
                        By.XPATH, './ancestor::div[@role="row"]//span[@dir="auto"]'
                    ).text
                    print(f"📩 New message from {chat_name}")

                    self.open_chat(chat)
                    incoming_msg = self.get_latest_incoming_message()

                    if incoming_msg and incoming_msg not in self.processed_messages:
                        # Generate response (via cloud AI – zero RAM usage)
                        reply = generate_response(incoming_msg)

                        # Human "thinking" delay
                        think_time = random.uniform(3, 10)
                        print(f"⏳ Thinking for {think_time:.1f}s...")
                        time.sleep(think_time)

                        # Send reply
                        self.send_message(reply)
                        print(f"💬 Reply: {reply}\n")

                        # Mark as processed
                        self.processed_messages.add(incoming_msg)

                # Wait before checking again
                time.sleep(check_interval)

            except KeyboardInterrupt:
                print("\n👋 Stopped by user.")
                break
            except Exception as e:
                print(f"⚠️ Error: {e}")
                time.sleep(check_interval * 2)

if __name__ == "__main__":
    bot = WhatsAppResponder()
    bot.run()