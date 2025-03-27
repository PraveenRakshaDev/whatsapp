from flask import Flask, request, jsonify
import requests
import datetime
import re

app = Flask(__name__)

# Your Gupshup credentials (replace with your actual API key and sandbox number)
GUPSHUP_API_KEY = "hiddbulkh9541upcsqjblraadvg6wie6"
GUPSHUP_SOURCE_NUMBER = "+917834811114"

# Function to send message to WhatsApp via Gupshup
def send_whatsapp_message(destination, message):
    payload = {
        "channel": "whatsapp",
        "source": GUPSHUP_SOURCE_NUMBER,
        "destination": destination,
        "message": message,
        "src.name": "TaskBot"
    }
    headers = {
        "apikey": GUPSHUP_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(
        "https://api.gupshup.io/sm/api/v1/msg",
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
    sender = data.get('payload', {}).get('payload', {}).get('source', '')
    
    # Pattern matching to detect task follow-up requests
    match = re.search(r"follow up on task (\d+)", incoming_message)
    
    if match:
        task_id = match.group(1)
        # Example: In real scenario, you’d query your DB for task details
        task_info = f"Task {task_id}: 'Submit report' is due today at 5 PM. Shall I remind you in 1 hour?"
        send_whatsapp_message(sender, task_info)
        
    elif "hi" in incoming_message or "hello" in incoming_message:
        welcome_message = "Hello! 👋 I am your Task Follow-Up Bot. You can type 'Follow up on task 101' and I’ll remind you!"
        send_whatsapp_message(sender, welcome_message)
        
    elif "remind me" in incoming_message:
        reminder_response = "✅ Reminder set! I’ll ping you again in 1 hour. Stay focused! 🚀"
        send_whatsapp_message(sender, reminder_response)
        
    else:
        fallback_message = "I didn't quite get that. Type something like 'Follow up on task 123' and I'll help you track it!"
        send_whatsapp_message(sender, fallback_message)

    return jsonify({"status": "received"}), 200

# Basic route
@app.route('/')
def home():
    return "Task Follow-Up Chatbot is live! 🚀"

if __name__ == '__main__':
    app.run(port=5000, debug=True)
