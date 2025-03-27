import os
import re
from flask import Flask, request, jsonify
import requests
from datetime import datetime
from functools import wraps

app = Flask(__name__)

# Configuration - Use environment variables in production!
GUPSHUP_API_KEY = 'sk_19a205f2aead48b7a41299f9013f0c4e'
GUPSHUP_SOURCE_NUMBER = '917834811114'
BOT_NAME ='devchatbottest'

# In-memory task storage (replace with database in production)
tasks = {}
user_sessions = {}

# Helper functions
def validate_phone_number(number):
    """Validate Indian phone numbers"""
    return re.match(r'^[6-9]\d{9}$', number)

def create_task(user_id, task_description, due_date=None):
    """Create a new task"""
    task_id = f"task_{len(tasks) + 1}"
    tasks[task_id] = {
        'user_id': user_id,
        'description': task_description,
        'due_date': due_date,
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    }
    return task_id

def get_user_tasks(user_id):
    """Get all tasks for a user"""
    return {k: v for k, v in tasks.items() if v['user_id'] == user_id}

def send_whatsapp_message(destination, message, context_id=None):
    """Send message via Gupshup API"""
    try:
        payload = {
            "channel": "whatsapp",
            "source": GUPSHUP_SOURCE_NUMBER,
            "destination": destination,
            "message": jsonify_message(message),
            "src.name": BOT_NAME
        }
        
        if context_id:
            payload["context"] = context_id

        headers = {
            "apikey": GUPSHUP_API_KEY,
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = requests.post(
            "https://api.gupshup.io/wa/api/v1/msg",
            data=payload,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        app.logger.error(f"Error sending message: {str(e)}")
        return None

def jsonify_message(text):
    """Format text message for Gupshup API"""
    return f'{{"type":"text","text":"{text}"}}'

def format_task_list(tasks_dict):
    """Format tasks into readable message"""
    if not tasks_dict:
        return "You have no tasks currently."
    
    message = "📝 Your Tasks:\n"
    for task_id, task in tasks_dict.items():
        status_icon = "✅" if task['status'] == 'completed' else "⏳"
        due_date = f"\n   Due: {task['due_date']}" if task['due_date'] else ""
        message += f"\n{status_icon} {task_id}: {task['description']}{due_date}"
    
    return message

# Webhook handler
@app.route('/gupshup-webhook', methods=['POST'])
def gupshup_webhook():
    try:
        data = request.json
        app.logger.info(f"Incoming webhook: {data}")

        payload = data.get('payload', {})
        message_data = payload.get('payload', {})
        incoming_message = message_data.get('text', '').lower()
        sender_number = payload.get('source', '')
        context_id = payload.get('id', '')

        if not validate_phone_number(sender_number):
            return jsonify({"error": "Invalid sender number"}), 400

        # Check if user has an active session
        session = user_sessions.get(sender_number, {'state': 'main_menu'})

        # Process message based on current state
        if session['state'] == 'main_menu':
            response = handle_main_menu(sender_number, incoming_message, context_id, session)
        elif session['state'] == 'awaiting_task_description':
            response = handle_task_description(sender_number, incoming_message, context_id, session)
        elif session['state'] == 'awaiting_due_date':
            response = handle_due_date(sender_number, incoming_message, context_id, session)
        else:
            response = handle_unknown_state(sender_number, context_id)

        return response

    except Exception as e:
        app.logger.error(f"Webhook processing error: {str(e)}")
        send_whatsapp_message(sender_number, "⚠️ An error occurred. Please try again.", context_id)
        return jsonify({"status": "error"}), 500

# State handlers
def handle_main_menu(sender_number, message, context_id, session):
    if message in ['hi', 'hello', 'hey']:
        welcome_msg = """👋 *Welcome to Task Manager Bot*!
        
Here's what I can do:
1️⃣ *Add Task* - Create a new task
2️⃣ *List Tasks* - Show all your tasks
3️⃣ *Complete Task* - Mark a task as done
4️⃣ *Delete Task* - Remove a task

Reply with the number or keyword of what you'd like to do."""
        send_whatsapp_message(sender_number, welcome_msg, context_id)
        return jsonify({"status": "success"}), 200

    elif any(x in message for x in ['add', 'create', 'new', '1']):
        user_sessions[sender_number] = {'state': 'awaiting_task_description'}
        send_whatsapp_message(sender_number, "✏️ Please describe your task:", context_id)
        return jsonify({"status": "success"}), 200

    elif any(x in message for x in ['list', 'show', 'view', '2']):
        tasks = get_user_tasks(sender_number)
        send_whatsapp_message(sender_number, format_task_list(tasks), context_id)
        return jsonify({"status": "success"}), 200

    elif any(x in message for x in ['complete', 'done', 'finish', '3']):
        tasks = get_user_tasks(sender_number)
        if not tasks:
            send_whatsapp_message(sender_number, "You have no tasks to complete.", context_id)
            return jsonify({"status": "success"}), 200
        
        user_sessions[sender_number] = {
            'state': 'awaiting_task_completion',
            'available_tasks': list(tasks.keys())
        }
        
        send_whatsapp_message(
            sender_number,
            f"Which task would you like to mark as complete?\n{format_task_list(tasks)}",
            context_id
        )
        return jsonify({"status": "success"}), 200

    else:
        send_whatsapp_message(
            sender_number,
            "I didn't understand that. Please say 'hi' to see menu options.",
            context_id
        )
        return jsonify({"status": "success"}), 200

def handle_task_description(sender_number, message, context_id, session):
    session['task_description'] = message
    session['state'] = 'awaiting_due_date'
    user_sessions[sender_number] = session
    
    send_whatsapp_message(
        sender_number,
        "📅 Would you like to add a due date? (Reply with date like 'tomorrow' or '15 Aug') or say 'skip'",
        context_id
    )
    return jsonify({"status": "success"}), 200

def handle_due_date(sender_number, message, context_id, session):
    due_date = None if message == 'skip' else message
    task_id = create_task(sender_number, session['task_description'], due_date)
    
    del user_sessions[sender_number]  # Clear session
    
    confirmation = f"✅ Task created successfully!\n\nTask ID: {task_id}\nDescription: {session['task_description']}"
    if due_date:
        confirmation += f"\nDue Date: {due_date}"
    
    send_whatsapp_message(sender_number, confirmation, context_id)
    return jsonify({"status": "success"}), 200

def handle_unknown_state(sender_number, context_id):
    send_whatsapp_message(
        sender_number,
        "⚠️ Session expired. Please start over by saying 'hi'.",
        context_id
    )
    return jsonify({"status": "success"}), 200

@app.route('/')
def home():
    return "Task Manager Chatbot is running!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)