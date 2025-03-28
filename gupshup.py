from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Configuration
# Configuration - Use environment variables in production!
GUPSHUP_API_KEY = 'sk_19a205f2aead48b7a41299f9013f0c4e'
GUPSHUP_SOURCE_NUMBER = '917834811114'
BOT_NAME ='devchatbottest'

# Basic task storage
tasks = {}

def send_whatsapp_message(destination, message):
    """Simplified message sending function"""
    try:
        payload = {
            "channel": "whatsapp",
            "source": GUPSHUP_SOURCE_NUMBER,
            "destination": destination,
            "message": f'{{"type":"text","text":"{message}"}}',
            "src.name": BOT_NAME
        }
        
        headers = {
            "apikey": GUPSHUP_API_KEY,
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = requests.post(
            "https://api.gupshup.io/wa/api/v1/msg",
            data=payload,
            headers=headers
        )
        return response.json()
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        return None

@app.route('/gupshup-webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        print("Received data:", data)  # Debug print
        
        # Extract basic information
        payload = data.get('payload', {})
        sender = payload.get('source', '')
        message = payload.get('payload', {}).get('text', '').lower()
        
        if not sender:
            return jsonify({"error": "Missing sender"}), 400

        # Basic command handling
        if message in ['hi', 'hello']:
            reply = "👋 Hello! I'm your task bot. Send 'add task' to create a task."
        elif 'add task' in message:
            task_id = f"task_{len(tasks)+1}"
            tasks[task_id] = {"description": message.replace('add task', '').strip(), "status": "pending"}
            reply = f"✅ Task added! ID: {task_id}"
        elif 'list tasks' in message:
            if not tasks:
                reply = "You have no tasks yet."
            else:
                reply = "📝 Your tasks:\n" + "\n".join([f"{id}: {task['description']}" for id, task in tasks.items()])
        else:
            reply = "Sorry, I didn't understand. Try 'hi' or 'add task'."
        
        send_whatsapp_message(sender, reply)
        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"Error in webhook: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/')
def home():
    return "WhatsApp Task Bot is running!"

if __name__ == '__main__':
    app.run(port=5000, debug=True)