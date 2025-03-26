from flask import Flask, Response, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import re
import os

apiKey  = os.getenv("GOOGLE_API_KEY")

app = Flask(__name__)
CORS(app)


def sendtoAi(prompt):
    genai.configure(api_key=apiKey)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)

    

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
    
                fetch('http://webai-production.up.railway.app/chatbot', {
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
    user_message = request.json.get('message', '')

    # 🤖 AI Response (Replace this with Google Gemini API)
    if "hello" in user_message.lower():
        bot_response = "Hello! How can I assist you today? 😊"
    elif "bye" in user_message.lower():
        bot_response = "Goodbye! Have a great day! 👋"
    else:
        bot_response = sendtoAi(user_message.lower())

    return jsonify({"response": bot_response})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
