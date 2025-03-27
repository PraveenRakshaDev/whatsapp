from flask import Flask, request, jsonify
import requests
import datetime
import re

app = Flask(__name__)

# Your Gupshup credentials (replace with your actual API key and sandbox number)
GUPSHUP_API_KEY = "hiddbulkh9541upcsqjblraadvg6wie6"
GUPSHUP_SOURCE_NUMBER = "+917834811114"

# Function to send message to WhatsApp via Gupshup
def send_whatsapp_message(destination, message, context_id=None):
    payload = {
        "channel": "whatsapp",
        "source": GUPSHUP_SOURCE_NUMBER,
        "destination": destination,
        "message": message,
        "src.name": "TaskBot"
    }
    
    # Add context ID if it's a reply to a message
    if context_id:
        payload["context"] = context_id  

    headers = {
        "apikey": GUPSHUP_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post(
        "https://api.gupshup.io/wa/api/v1/msg",
        data=payload,
        headers=headers
    )
    print(f"Message sent response: {response.text}")
    return response.text


# Route for Gupshup webhook callback
@app.route('/gupshup-webhook', methods=['POST'])
def gupshup_webhook():
    data = request.json
    print(f"Incoming webhook: {data}")

    incoming_message = data.get('payload', {}).get('payload', {}).get('text', '').lower()
    sender = data.get('payload', {}).get('source', '')
    context_id = data.get('payload', {}).get('id', '')  # Extract message ID

    if "hi" in incoming_message or "hello" in incoming_message:
        welcome_message = "Hello! 👋 I am your Task Follow-Up Bot. How can I assist you today?"
        send_whatsapp_message(sender, welcome_message, context_id)  # Pass context_id

    elif "follow up on task" in incoming_message:
        task_info = "Task follow-up request received! 🚀"
        send_whatsapp_message(sender, task_info, context_id)

    else:
        fallback_message = "I didn't quite understand. Try saying 'Follow up on task 123'."
        send_whatsapp_message(sender, fallback_message, context_id)

    return jsonify({"status": "received"}), 200
# Basic route
@app.route('/')
def home():
    return "Task Follow-Up Chatbot is live! 🚀"

if __name__ == '__main__':
    app.run(port=5000, debug=True)
