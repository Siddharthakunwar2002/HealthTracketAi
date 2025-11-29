from flask import Flask, render_template, request, jsonify
from chatbot import HealthChatbot
import nltk
import os
import json

# Download required NLTK data
nltk.download('punkt')
nltk.download('wordnet')

app = Flask(__name__)
chatbot = HealthChatbot()

# Create necessary directories
os.makedirs('data', exist_ok=True)
os.makedirs('templates', exist_ok=True)

# Create a basic intents file if it doesn't exist
if not os.path.exists('data/intents.json'):
    intents_data = {
        "intents": [
            {
                "tag": "greeting",
                "patterns": ["Hi", "Hello", "Hey", "How are you", "Good day", "Good morning", "Good afternoon", "Good evening"],
                "responses": [
                    "Hello! I'm your AI health assistant. How can I help you today?",
                    "Hi there! I'm here to provide health information and support. What would you like to know?",
                    "Hello! I'm your virtual health companion. How can I assist you with your health concerns today?"
                ]
            },
            {
                "tag": "goodbye",
                "patterns": ["Bye", "See you later", "Goodbye", "Take care", "See you", "Bye bye"],
                "responses": [
                    "Goodbye! Remember to take care of your health!",
                    "See you later! Stay healthy and hydrated!",
                    "Take care! Don't forget to maintain a healthy lifestyle!",
                    "Bye! Remember to get enough rest and exercise!"
                ]
            }
        ]
    }
    with open('data/intents.json', 'w', encoding='utf-8') as f:
        json.dump(intents_data, f, indent=4, ensure_ascii=False)

# Initialize the chatbot
chatbot.load_data()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
        
    response = chatbot.get_response(user_message)
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=True) 