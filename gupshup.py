from flask import Flask, request, jsonify
import requests
import datetime
import re

app = Flask(__name__)

# Your Gupshup credentials (replace with your actual API key and sandbox number)
GUPSHUP_API_KEY = "sk_19a205f2aead48b7a41299f9013f0c4e"
GUPSHUP_SOURCE_NUMBER = "917834811114"

# Function to send message to WhatsApp via Gupshup
def send_whatsapp_message( message, sender_number, context_id=None):
    payload = {
        "channel": "whatsapp",
        "source": GUPSHUP_SOURCE_NUMBER,
        "destination": sender_number,
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
# Temporary storage for user responses
user_data = {}  # Global counter for task IDs

# Webhook to handle incoming messages
@app.route('/gupshup-webhook', methods=['POST'])
def gupshup_webhook():
    data = request.json
    print(f"Incoming webhook: {data}")

    incoming_message = data.get('payload', {}).get('payload', {}).get('text', '').lower()
    sender_number = data.get('payload', {}).get('source', '')  # Get sender's number
    context_id = data.get('payload', {}).get('id', '')  # Message ID

    if not incoming_message:
        print("Ignoring empty message")
        return jsonify({"status": "ignored"}), 200

    # Start Sign-off process
    if "signoff" in incoming_message:
        user_data[sender_number] = {
            "CRM Ref": None,
            "Remarks": None,
            "Pipeline Stage": None,
            "Case Locking Status": None,
            "Incoming Commercial Quote Status": None,
            "POC / Demo Status": None,
            "Joint Meeting Status": None,
            "Budget Approval Status": None
        }
        send_whatsapp_message(
            "📝 *Sign-off Process Started!*\n\nPlease provide *CRM Reference Number*:", 
            sender_number, context_id
        )
    elif sender_number in user_data and user_data[sender_number]["CRM Ref"] is None:
        user_data[sender_number]["CRM Ref"] = incoming_message
        send_whatsapp_message("📌 *CRM Ref Saved!* Now enter *Remarks*:", sender_number, context_id)
    elif sender_number in user_data and user_data[sender_number]["Remarks"] is None:
        user_data[sender_number]["Remarks"] = incoming_message
        send_whatsapp_message("📊 *Remarks Saved!* Now enter *Pipeline Stage*:", sender_number, context_id)
    elif sender_number in user_data and user_data[sender_number]["Pipeline Stage"] is None:
        user_data[sender_number]["Pipeline Stage"] = incoming_message
        send_whatsapp_message("🔒 *Pipeline Stage Saved!* Now enter *Case Locking Status*:", sender_number, context_id)
    elif sender_number in user_data and user_data[sender_number]["Case Locking Status"] is None:
        user_data[sender_number]["Case Locking Status"] = incoming_message
        send_whatsapp_message("📑 *Case Locking Status Saved!* Now enter *Incoming Commercial Quote Status*:", sender_number, context_id)
    elif sender_number in user_data and user_data[sender_number]["Incoming Commercial Quote Status"] is None:
        user_data[sender_number]["Incoming Commercial Quote Status"] = incoming_message
        send_whatsapp_message("📜 *Quote Status Saved!* Now enter *POC / Demo Status*:", sender_number, context_id)
    elif sender_number in user_data and user_data[sender_number]["POC / Demo Status"] is None:
        user_data[sender_number]["POC / Demo Status"] = incoming_message
        send_whatsapp_message("🎤 *POC / Demo Status Saved!* Now enter *Joint Meeting Status*:", sender_number, context_id)
    elif sender_number in user_data and user_data[sender_number]["Joint Meeting Status"] is None:
        user_data[sender_number]["Joint Meeting Status"] = incoming_message
        send_whatsapp_message("💰 *Joint Meeting Status Saved!* Now enter *Budget Approval Status*:", sender_number, context_id)
    elif sender_number in user_data and user_data[sender_number]["Budget Approval Status"] is None:
        user_data[sender_number]["Budget Approval Status"] = incoming_message
        # Confirm all details
        confirmation_message = f"""✅ *Sign-off Complete!*
📌 CRM Ref: {user_data[sender_number]['CRM Ref']}
📝 Remarks: {user_data[sender_number]['Remarks']}
📊 Pipeline Stage: {user_data[sender_number]['Pipeline Stage']}
🔒 Case Locking Status: {user_data[sender_number]['Case Locking Status']}
📑 Incoming Quote Status: {user_data[sender_number]['Incoming Commercial Quote Status']}
🎤 POC/Demo Status: {user_data[sender_number]['POC / Demo Status']}
💼 Joint Meeting Status: {user_data[sender_number]['Joint Meeting Status']}
💰 Budget Approval Status: {user_data[sender_number]['Budget Approval Status']}"""

        send_whatsapp_message(confirmation_message, sender_number, context_id)
        del user_data[sender_number]  # Remove after completion
    else:
        send_whatsapp_message("I didn't understand that. Try sending 'signoff' to start.", sender_number, context_id)

    return jsonify({"status": "success"}), 200
# Basic route
@app.route('/')
def home():
    return "Task Follow-Up Chatbot is live! 🚀"

if __name__ == '__main__':
    app.run(port=5000, debug=True)
