import json
import nltk
from nltk.stem import WordNetLemmatizer
import random
import os
from difflib import SequenceMatcher
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthChatbotModel:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.intents = None
        self.ignore_words = ['?', '!', '.', ',']
        logger.info("HealthChatbotModel initialized")
        
    def load_data(self, intents_file):
        try:
            logger.info(f"Loading intents from {intents_file}")
            with open(intents_file, 'r', encoding='utf-8') as file:
                self.intents = json.load(file)
            logger.info("Intents loaded successfully")
        except Exception as e:
            logger.error(f"Error loading intents: {str(e)}")
            raise
            
    def prepare_training_data(self):
        # No training needed for pattern matching
        pass
        
    def build_model(self):
        # No model building needed for pattern matching
        pass
        
    def train_model(self, epochs=200, batch_size=5):
        # No training needed for pattern matching
        pass
        
    def save_model(self, model_path='model/health_chatbot_model.h5'):
        try:
            # Save intents data
            if not os.path.exists('model'):
                os.makedirs('model')
            with open('model/intents.json', 'w', encoding='utf-8') as f:
                json.dump(self.intents, f, ensure_ascii=False, indent=2)
            logger.info("Model saved successfully")
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise
            
    def load_saved_model(self, model_path='model/health_chatbot_model.h5'):
        try:
            intents_path = 'model/intents.json'
            if os.path.exists(intents_path):
                logger.info(f"Loading saved model from {intents_path}")
                with open(intents_path, 'r', encoding='utf-8') as f:
                    self.intents = json.load(f)
                logger.info("Saved model loaded successfully")
                return True
            logger.info("No saved model found")
            return False
        except Exception as e:
            logger.error(f"Error loading saved model: {str(e)}")
            return False
        
    def get_similarity_score(self, str1, str2):
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
        
    def get_response(self, sentence):
        try:
            if not self.intents:
                logger.error("Intents not loaded")
                return "I'm not properly initialized. Please try again later."
            
            logger.info(f"Processing message: {sentence}")
            
            # Tokenize and lemmatize the input sentence
            sentence_words = nltk.word_tokenize(sentence)
            sentence_words = [self.lemmatizer.lemmatize(word.lower()) for word in sentence_words if word not in self.ignore_words]
            
            best_match = None
            highest_similarity = 0.5  # Minimum similarity threshold
            
            # Find the best matching intent
            for intent in self.intents['intents']:
                for pattern in intent['patterns']:
                    pattern_words = nltk.word_tokenize(pattern)
                    pattern_words = [self.lemmatizer.lemmatize(word.lower()) for word in pattern_words if word not in self.ignore_words]
                    
                    # Calculate similarity between input and pattern
                    similarity = self.get_similarity_score(' '.join(sentence_words), ' '.join(pattern_words))
                    
                    if similarity > highest_similarity:
                        highest_similarity = similarity
                        best_match = intent
            
            if best_match:
                response = random.choice(best_match['responses'])
                logger.info(f"Found response for intent: {best_match['tag']}")
                return response
            else:
                logger.info("No matching intent found")
                return "I'm not sure I understand. Could you please rephrase that?"
                
        except Exception as e:
            logger.error(f"Error getting response: {str(e)}")
            return "I apologize, but I encountered an error. Please try again."

# Example usage
if __name__ == "__main__":
    # Download required NLTK data
    nltk.download('punkt')
    nltk.download('wordnet')
    
    # Initialize the chatbot
    chatbot = HealthChatbotModel()
    chatbot.load_data('data/intents.json')
    chatbot.save_model() 