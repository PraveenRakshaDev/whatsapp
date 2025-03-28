from flask import Flask, request, jsonify
import requests
import datetime
import re

app = Flask(__name__)

# Your Gupshup credentials (replace with your actual API key and sandbox number)
GUPSHUP_API_KEY = "sk_19a205f2aead48b7a41299f9013f0c4e"
GUPSHUP_SOURCE_NUMBER = "917834811114"

# Function to send message to WhatsApp via Gupshup
def send_whatsapp_message( message, context_id=None):
    payload = {
        "channel": "whatsapp",
        "source": GUPSHUP_SOURCE_NUMBER,
        "destination": 917063908412,
        "message": message,
        "src.name": "devchatbottest"
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

# Store user tasks { user_id: [{task_id: str, description: str, status: str}] }
user_tasks = {}
user_context = {}  # Tracks the last action per user
task_counter = 1  # Global counter for task IDs

@app.route('/gupshup-webhook', methods=['POST'])
def gupshup_webhook():
    global task_counter

    data = request.json
    print(f"Incoming webhook: {data}")

    incoming_message = data.get('payload', {}).get('payload', {}).get('text', '').strip()
    sender_id = data.get('payload', {}).get('source', '')  # Unique user ID
    context_id = data.get('payload', {}).get('id', '')  # Message ID

    # Ignore empty messages
    if not incoming_message:
        return jsonify({"status": "ignored"}), 200

    # Retrieve user context and tasks
    last_action = user_context.get(sender_id, "")
    user_tasks.setdefault(sender_id, [])

    # Greet user and show menu
    if incoming_message.lower() in ["hi", "hello"]:
        welcome_message = """👋 *Welcome to Task Manager Bot!*  

🔹 I can help you manage your tasks efficiently.  
Here’s what I can do for you:  

1️⃣ *Add Task* - Create a new task  
2️⃣ *List Tasks* - Show all your tasks  
3️⃣ *Complete Task* - Mark a task as done  
4️⃣ *Delete Task* - Remove a task  

👉 Reply with the number or keyword to proceed."""
        send_whatsapp_message(welcome_message, context_id)
        user_context[sender_id] = ""  # Reset context

    # Add Task Flow
    elif incoming_message.lower() in ["add task", "1"]:
        send_whatsapp_message("✏️ *Please describe your task.*\nExample: 'Submit report by 5 PM'.", context_id)
        user_context[sender_id] = "adding_task"

    elif last_action == "adding_task":
        task_id = task_counter
        task_counter += 1  # Increment for next task
        user_tasks[sender_id].append({"task_id": task_id, "description": incoming_message, "status": "Pending"})
        send_whatsapp_message(f"✅ *Task added successfully!*\nYour task: '{incoming_message}'", context_id)
        user_context[sender_id] = ""  # Reset context

    # List Tasks
    elif incoming_message.lower() in ["list tasks", "2"]:
        if not user_tasks[sender_id]:
            send_whatsapp_message("📋 *You have no tasks yet!*\nUse 'Add Task' to create one.", context_id)
        else:
            task_list = "\n".join([f"{task['task_id']}. {task['description']} - *{task['status']}*" for task in user_tasks[sender_id]])
            send_whatsapp_message(f"📋 *Your Tasks:*\n{task_list}\n\n👉 Reply 'Complete Task <ID>' or 'Delete Task <ID>'.", context_id)
        user_context[sender_id] = ""

    # Complete Task
    elif incoming_message.lower().startswith("complete task") or incoming_message.startswith("3"):
        try:
            task_id = int(incoming_message.split()[-1])
            for task in user_tasks[sender_id]:
                if task["task_id"] == task_id:
                    task["status"] = "Completed"
                    send_whatsapp_message(f"✅ *Task {task_id} marked as completed!*", context_id)
                    break
            else:
                send_whatsapp_message(f"⚠️ *Task {task_id} not found!*", context_id)
        except ValueError:
            send_whatsapp_message("⚠️ *Invalid format!*\nTry 'Complete Task <ID>'.", context_id)

    # Delete Task
    elif incoming_message.lower().startswith("delete task") or incoming_message.startswith("4"):
        try:
            task_id = int(incoming_message.split()[-1])
            user_tasks[sender_id] = [task for task in user_tasks[sender_id] if task["task_id"] != task_id]
            send_whatsapp_message(f"🗑️ *Task {task_id} deleted successfully!*", context_id)
        except ValueError:
            send_whatsapp_message("⚠️ *Invalid format!*\nTry 'Delete Task <ID>'.", context_id)

    # Follow-up on Task
    elif "follow up on task" in incoming_message.lower():
        task_num = ''.join(filter(str.isdigit, incoming_message)) or "UNKNOWN"
        send_whatsapp_message(f"🚀 *Tracking Task {task_num}!*", context_id)

    # Default Response for Unrecognized Messages
    else:
        send_whatsapp_message("❓ *I didn't understand that.*\nTry 'hi' to see available options.", context_id)

    return jsonify({"status": "success"}), 200

# Basic route
@app.route('/')
def home():
    return "Task Follow-Up Chatbot is live! 🚀"

if __name__ == '__main__':
    app.run(port=5000, debug=True)
