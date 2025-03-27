from flask import Flask, Response, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import re
import os
import json
import requests
import uuid

apiKey  = os.getenv("GOOGLE_API_KEY")
USER_HISTORIES = {}  # {user_id: [{"user": "...", "bot": "..."}, ...]}
USER_AGENT_CHATS = {}  # {user_id: {"is_agent_chat": bool, "telegram_chat_id": str}}
ACTIVE_CHATS = {}

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_AGENT_CHAT_ID = os.getenv("TELEGRAM_AGENT_CHAT_ID")

app = Flask(__name__)
CORS(app)

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    response = requests.post(url, json=payload)
    return response.status_code == 200


def get_request_domain():
    """Extract the domain from Origin or Referer headers."""
    origin = request.headers.get('Origin')
    if origin:
        return origin  # e.g., "https://sunnyshades.com"
    
    referer = request.headers.get('Referer')
    if referer:
        parsed = urlparse(referer)
        return f"{parsed.scheme}://{parsed.netloc}"  # e.g., "https://sunnyshades.com"
    
    return "Unknown"  # Fallback if neither header is present
    

def sendtoAi(prompt, history=None):
    # Configure Gemini
    genai.configure(api_key=apiKey)
    model = genai.GenerativeModel("gemini-1.5-flash")

    # Convert business JSON to string
    business_json_str = json.dumps(BUSINESS_JSON)

    # Handle conversation history (default to empty list if None)
    history = history or []
    history_str = json.dumps(history) if history else "[]"

    # Construct the full prompt
    full_prompt = (
        f"Business Context: {business_json_str}\n"
        f"Conversation History: {history_str}\n"
        f"User Query: \"{prompt}\"\n"
        "Instructions: Respond to the user's query using the provided business context and history. "
        
    )

    
    response = model.generate_content(full_prompt)

    
    return response.text


@app.route('/chatbot.js', methods=['GET'])
def chatbot_js():
    js_code = """
    (function() {
        let existingContainer = document.getElementById('chatbot-container');
        if (existingContainer) {
            existingContainer.parentNode.removeChild(existingContainer);
        }

        var chatbotContainer = document.createElement('div');
        chatbotContainer.id = 'chatbot-container';
        chatbotContainer.style.position = 'fixed';
        chatbotContainer.style.bottom = '20px';
        chatbotContainer.style.right = '20px';
        chatbotContainer.style.width = '350px';
        chatbotContainer.style.height = '500px';
        chatbotContainer.style.background = '#ffffff';
        chatbotContainer.style.borderRadius = '10px';
        chatbotContainer.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
        chatbotContainer.style.display = 'none';
        chatbotContainer.style.flexDirection = 'column';
        chatbotContainer.style.justifyContent = 'space-between';
        chatbotContainer.style.fontFamily = 'Arial, sans-serif';

        chatbotContainer.innerHTML = `
            <div id='chatbot-header' style='background: #007bff; color: white; padding: 15px; text-align: center; font-weight: bold; cursor: pointer; border-top-left-radius: 10px; border-top-right-radius: 10px; display: flex; justify-content: space-between;'>
                <span>Chat with AI</span>
                <button id='close-chatbot' style='background: transparent; border: none; color: white; font-size: 16px; cursor: pointer;'>✕</button>
            </div>
            <div id='chatbot-messages' style='flex: 1; padding: 10px; overflow-y: auto; max-height: 400px;'></div>
            <div id='chatbot-input-area' style='display: flex; padding: 10px; border-top: 1px solid #ccc;'>
                <input id='chatbot-input' type='text' placeholder='Type a message...' style='flex: 1; border: none; padding: 10px; border-radius: 5px;'>
                <button id='send-message' style='background: #007bff; color: white; border: none; padding: 10px 15px; cursor: pointer; border-radius: 5px; margin-left: 5px;'>Send</button>
            </div>
        `;

        document.body.appendChild(chatbotContainer);

        var toggleButton = document.createElement('button');
        toggleButton.innerText = 'Chat 💬';
        toggleButton.id = 'chatbot-toggle';
        toggleButton.style.position = 'fixed';
        toggleButton.style.bottom = '20px';
        toggleButton.style.right = '20px';
        toggleButton.style.background = '#007bff';
        toggleButton.style.color = 'white';
        toggleButton.style.border = 'none';
        toggleButton.style.padding = '10px 15px';
        toggleButton.style.borderRadius = '5px';
        toggleButton.style.cursor = 'pointer';
        toggleButton.style.boxShadow = '0 2px 5px rgba(0, 0, 0, 0.2)';
        document.body.appendChild(toggleButton);

        document.getElementById('chatbot-toggle').addEventListener('click', function() {
            if (chatbotContainer.style.display === 'none') {
                chatbotContainer.style.display = 'flex';
                toggleButton.style.display = 'none';
            } else {
                chatbotContainer.style.display = 'none';
                toggleButton.style.display = 'block';
            }
        });

        document.getElementById('close-chatbot').addEventListener('click', function() {
            chatbotContainer.style.display = 'none';
            toggleButton.style.display = 'block';
        });

        function sendMessage() {
            let inputField = document.getElementById('chatbot-input');
            let message = inputField.value.trim();
            if (message !== '') {
                let messagesDiv = document.getElementById('chatbot-messages');

                let userMessage = document.createElement('div');
                userMessage.innerHTML = message;
                userMessage.style.background = '#007bff';
                userMessage.style.color = 'white';
                userMessage.style.padding = '10px';
                userMessage.style.margin = '5px';
                userMessage.style.borderRadius = '10px';
                userMessage.style.alignSelf = 'flex-end';
                messagesDiv.appendChild(userMessage);

                inputField.value = '';

                // Add typing indicator
                let typingMessage = document.createElement('div');
                typingMessage.innerHTML = 'Typing...';
                typingMessage.style.background = '#e9ecef';
                typingMessage.style.color = '#333';
                typingMessage.style.padding = '10px';
                typingMessage.style.margin = '5px';
                typingMessage.style.borderRadius = '10px';
                typingMessage.style.alignSelf = 'flex-start';
                messagesDiv.appendChild(typingMessage);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
                fetch('https://webai-production.up.railway.app/chatbot', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ message: message })
                })
                .then(response => response.json())
                .then(data => {
                    messagesDiv.removeChild(typingMessage); // Remove typing indicator
                    let botMessage = document.createElement('div');
                    botMessage.innerHTML = data.response;
                    botMessage.style.background = '#e9ecef';
                    botMessage.style.color = '#333';
                    botMessage.style.padding = '10px';
                    botMessage.style.margin = '5px';
                    botMessage.style.borderRadius = '10px';
                    botMessage.style.alignSelf = 'flex-start';
                    messagesDiv.appendChild(botMessage);
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                })
                .catch(error => {
                    messagesDiv.removeChild(typingMessage); // Remove typing indicator on error
                    console.error('Error:', error);
                    let errorMessage = document.createElement('div');
                    errorMessage.innerHTML = 'Oops! Something went wrong.';
                    errorMessage.style.background = '#ffcccc';
                    errorMessage.style.color = '#333';
                    errorMessage.style.padding = '10px';
                    errorMessage.style.margin = '5px';
                    errorMessage.style.borderRadius = '10px';
                    errorMessage.style.alignSelf = 'flex-start';
                    messagesDiv.appendChild(errorMessage);
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                });
            }
        }

        document.getElementById('send-message').addEventListener('click', sendMessage);
        document.getElementById('chatbot-input').addEventListener('keypress', function(event) {
            if (event.key === 'Enter') sendMessage();
        });
    })();
    """
    return Response(js_code, mimetype='application/javascript')

@app.route('/chatbot', methods=['POST'])
def chatbot():
    data = request.json
    user_message = data.get('message', '').lower()
    user_id = data.get('userId', str(uuid.uuid4()))
    domain = get_request_domain()
    print(f"Chat request from user {user_id} at domain: {domain} - Message: {user_message}")

    # Initialize user history and agent chat state
    if user_id not in USER_HISTORIES:
        USER_HISTORIES[user_id] = []
    if user_id not in USER_AGENT_CHATS:
        USER_AGENT_CHATS[user_id] = {"is_agent_chat": False, "telegram_chat_id": None}
    
    user_history = USER_HISTORIES[user_id]
    user_agent_chat = USER_AGENT_CHATS[user_id]

    # Check if user wants to chat with agent
    if "chat with agent" in user_message or "talk to agent" in user_message:
        user_agent_chat["is_agent_chat"] = True
        user_agent_chat["telegram_chat_id"] = TELEGRAM_AGENT_CHAT_ID
        message_to_agent = f"[{user_id}] User requested agent chat: {user_message}"
        send_telegram_message(TELEGRAM_AGENT_CHAT_ID, message_to_agent)
        bot_response = "I’ve notified an agent. They’ll join the chat soon."
        user_history.append({"user": user_message, "bot": bot_response})
        return jsonify({"response": bot_response})

    # Route to agent if in agent chat mode
    if user_agent_chat["is_agent_chat"]:
        message_to_agent = f"[{user_id}] {user_message}"
        send_telegram_message(TELEGRAM_AGENT_CHAT_ID, message_to_agent)
        bot_response = "Message sent to agent. Please wait for their reply."
        user_history.append({"user": user_message, "bot": bot_response})
        return jsonify({"response": bot_response})

    # Otherwise, use AI
    bot_response = sendtoAi(user_message.lower(), user_history)
    user_history.append({"user": user_message, "bot": bot_response})
    if len(user_history) > 10:
        user_history.pop(0)

    return jsonify({"response": bot_response})

@app.route('/telegram_webhook', methods=['POST'])
def telegram_webhook():
    update = request.json
    if "message" in update:
        message = update["message"]
        chat_id = str(message["chat"]["id"])
        text = message["text"]

        # Check if this is from the agent
        if chat_id == TELEGRAM_AGENT_CHAT_ID:
            # Extract user_id from agent's reply (e.g., "[user_abc123] Hi there")
            try:
                user_id_start = text.index("[") + 1
                user_id_end = text.index("]")
                user_id = text[user_id_start:user_id_end]
                agent_reply = text[user_id_end + 1:].strip()

                # Route reply to user's chat
                if user_id in USER_HISTORIES:
                    USER_HISTORIES[user_id].append({"user": "(agent)", "bot": agent_reply})
                    # Notify user via their chat session
                    if user_id in ACTIVE_CHATS:
                        ACTIVE_CHATS[user_id].append({"response": f"Agent: {agent_reply}"})
                    else:
                        # If no active connection, store for next request (optional)
                        print(f"Agent reply for {user_id} stored: {agent_reply}")
            except ValueError:
                send_telegram_message(TELEGRAM_AGENT_CHAT_ID, "Please include [user_id] in your reply, e.g., [user_abc123] Hi")
    
    return jsonify({"status": "ok"})

BUSINESS_JSON = {
  "business": {
    "name": "Sunny Shades",
    "description": "Your one-stop shop for premium sunglasses.",
    "contact": {
      "phone": "+1-800-555-1234",
      "support_email": "support@sunnyshades.com",
      "sales_email": "sales@sunnyshades.com"
    },
    "address": {
      "street": "123 Sunshine Ave",
      "city": "Sunnyville",
      "state": "CA",
      "zip": "90210",
      "country": "USA"
    },
    "policies": {
      "return": {
        "timeframe": "30 days",
        "conditions": "Items must be unused, in original packaging, with receipt.",
        "process": "Contact support@sunnyshades.com to initiate a return."
      },
      "refund": {
        "timeframe": "14 days after return approval",
        "conditions": "Refunds issued to original payment method.",
        "exceptions": "Custom orders are non-refundable."
      },
      "warranty": {
        "duration": "1 year",
        "coverage": "Manufacturing defects only."
      }
    },
    "products": [
      {
        "id": "SS001",
        "name": "Ray-Ban Aviator",
        "category": "sports",
        "price": 150.00,
        "description": "Classic aviator style, ideal for sports and outdoor activities.",
        "attributes": {
          "color": "Black",
          "lens_type": "Polarized",
          "material": "Metal"
        },
        "stock": 25
      },
      {
        "id": "SS002",
        "name": "Gucci Round",
        "category": "fashion",
        "price": 300.00,
        "description": "Trendy round frames for a stylish look.",
        "attributes": {
          "color": "Gold",
          "lens_type": "Tinted",
          "material": "Acetate"
        },
        "stock": 15
      },
      {
        "id": "SS003",
        "name": "Polaroid Classic",
        "category": "budget",
        "price": 50.00,
        "description": "Affordable and reliable everyday sunglasses.",
        "attributes": {
          "color": "Matte Black",
          "lens_type": "UV Protection",
          "material": "Plastic"
        },
        "stock": 50
      }
    ],
    "services": {
      "appointments": {
        "description": "In-store try-ons or consultations.",
        "availability": "Monday-Friday, 10:00 AM - 6:00 PM PST",
        "booking_process": "Provide preferred date and time; confirmation sent via email."
      },
      "support": {
        "description": "Assistance with orders, returns, or repairs.",
        "contact": "support@sunnyshades.com",
        "response_time": "Within 24 hours"
      }
    }
  }
}

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
