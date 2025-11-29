import json
import random
import numpy as np
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import os
from nltk.corpus import stopwords

# Download required NLTK data
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('omw-1.4')
nltk.download('stopwords')

class HealthChatbot:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.vectorizer = TfidfVectorizer()
        self.patterns = []
        self.responses = []
        self.context = {}
        self.stop_words = set(stopwords.words('english'))
        
        # Health topic categories with more detailed responses
        self.categories = {
            'diet': ['nutrition', 'food', 'diet', 'eating', 'meal', 'weight', 'healthy eating'],
            'exercise': ['exercise', 'workout', 'fitness', 'training', 'sport', 'physical activity'],
            'mental': ['mental', 'stress', 'anxiety', 'depression', 'mood', 'emotional', 'wellbeing'],
            'sleep': ['sleep', 'rest', 'insomnia', 'tired', 'fatigue', 'bedtime'],
            'general': ['health', 'wellness', 'lifestyle', 'prevention', 'healthy living']
        }
        
        # Load intents first
        self.intents = self.load_intents()
        
        # Then prepare data
        self.prepare_data()
        
        # Fallback responses
        self.fallback_responses = [
            "I'm sorry, I don't have specific information about that topic yet. However, I can help you with general health advice, nutrition, exercise, mental health, sleep, and many other health-related topics. What would you like to know about?",
            "I'm not sure about that specific topic, but I'd be happy to help you with general health and wellness information. What would you like to learn about?",
            "While I don't have detailed information about that particular topic, I can provide guidance on various health topics like nutrition, exercise, mental health, and more. What interests you?",
            "I'm still learning about that topic, but I can help you with many other health-related questions. Would you like to know about general health, nutrition, exercise, or mental wellness?",
            "I don't have specific information about that yet, but I can help you with general health advice and wellness tips. What would you like to know about?"
        ]

    def load_intents(self):
        try:
            with open('data/intents.json', 'r', encoding='utf-8') as file:
                return json.load(file)['intents']
        except Exception as e:
            print(f"Error loading intents: {e}")
            return []

    def prepare_data(self):
        for intent in self.intents:
            for pattern in intent['patterns']:
                self.patterns.append(pattern)
                self.responses.append(intent['responses'])
        
        # Create TF-IDF vectors
        self.pattern_vectors = self.vectorizer.fit_transform(self.patterns)

    def preprocess_text(self, text):
        # Tokenize
        tokens = word_tokenize(text.lower())
        
        # Remove stop words and lemmatize
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens if token not in self.stop_words]
        
        return tokens

    def get_topic_category(self, text):
        text = text.lower()
        max_matches = 0
        best_category = 'general'
        
        for category, keywords in self.categories.items():
            matches = sum(1 for keyword in keywords if keyword in text)
            if matches > max_matches:
                max_matches = matches
                best_category = category
        
        return best_category

    def get_response(self, user_input):
        if not user_input.strip():
            return "I didn't catch that. Could you please repeat your question?"

        # Preprocess user input
        processed_input = self.preprocess_text(user_input)
        
        # Find matching intent
        best_match = None
        highest_score = 0

        for intent in self.intents:
            score = 0
            for pattern in intent['patterns']:
                pattern_tokens = self.preprocess_text(pattern)
                # Calculate similarity score
                common_words = set(processed_input) & set(pattern_tokens)
                if common_words:
                    score = len(common_words) / max(len(processed_input), len(pattern_tokens))
                    if score > highest_score:
                        highest_score = score
                        best_match = intent

        # If we have a good match, return a random response from that intent
        if best_match and highest_score > 0.3:  # Threshold for matching
            return random.choice(best_match['responses'])
        
        # If no good match found, return a fallback response
        return random.choice(self.fallback_responses)

    def get_detailed_response(self, category, query):
        if category == 'diet':
            return self.get_diet_response(query)
        elif category == 'exercise':
            return self.get_exercise_response(query)
        elif category == 'mental':
            return self.get_mental_health_response(query)
        elif category == 'sleep':
            return self.get_sleep_response(query)
        else:
            return self.get_general_health_response(query)

    def get_diet_response(self, query):
        if 'weight loss' in query.lower():
            return """Let me help you with a sustainable approach to weight management! 🎯

Here's a comprehensive guide:

1. **Smart Eating Habits**:
   - Eat mindfully and slowly
   - Use smaller plates
   - Stay hydrated
   - Plan your meals ahead

2. **Balanced Nutrition**:
   - Focus on whole foods
   - Include protein in each meal
   - Choose complex carbs
   - Add healthy fats

3. **Practical Tips**:
   - Keep a food journal
   - Cook at home more often
   - Read nutrition labels
   - Stay consistent

Would you like specific meal suggestions or a sample meal plan?"""
        else:
            return """Let's talk about nourishing your body! 🥗

Here's a balanced approach to nutrition:

1. **Build Your Plate**:
   - 50% vegetables and fruits
   - 25% lean proteins
   - 25% whole grains
   - Add healthy fats

2. **Smart Choices**:
   - Choose whole foods over processed
   - Include a variety of colors
   - Stay hydrated
   - Practice portion control

3. **Meal Planning Tips**:
   - Plan your meals ahead
   - Prep ingredients in advance
   - Keep healthy snacks handy
   - Listen to your body's cues

What specific aspect of nutrition would you like to explore?"""

    def get_exercise_response(self, query):
        if 'beginner' in query.lower():
            return """Let's start your fitness journey! 🌟

Here's a beginner-friendly plan:

1. **Week 1-2: Foundation**
   - 10-15 minute walks daily
   - Basic stretching
   - Bodyweight squats (10 reps)
   - Modified push-ups

2. **Week 3-4: Building Up**
   - 20-30 minute walks
   - Basic yoga poses
   - Lunges (10 each leg)
   - Plank (20 seconds)

3. **Week 5-6: Progress**
   - 30-45 minute walks
   - Full body stretches
   - Basic circuit training
   - Light cardio

Remember: Start slow and build gradually! Would you like specific exercise demonstrations?"""
        else:
            return """Let's get moving! 💪

Here's a balanced fitness approach:

1. **Cardiovascular Exercise**:
   - Walking, running, cycling
   - Swimming, dancing
   - 150 minutes weekly
   - Mix of intensities

2. **Strength Training**:
   - Bodyweight exercises
   - Light weights
   - 2-3 times weekly
   - Focus on form

3. **Flexibility & Balance**:
   - Daily stretching
   - Yoga or Pilates
   - Balance exercises
   - Mind-body connection

What's your current fitness level? I can provide more specific recommendations!"""

    def get_mental_health_response(self, query):
        if 'stress' in query.lower():
            return """Let's manage stress together! 🧘‍♀️

Here are effective stress management techniques:

1. **Quick Relief**:
   - Deep breathing exercises
   - Progressive muscle relaxation
   - Mindful meditation
   - Quick physical activity

2. **Daily Practices**:
   - Regular exercise
   - Adequate sleep
   - Healthy diet
   - Social connections

3. **Long-term Strategies**:
   - Time management
   - Setting boundaries
   - Regular self-care
   - Professional support if needed

Would you like specific relaxation techniques or a daily stress management plan?"""
        else:
            return """Let's focus on your mental wellbeing! 🌟

Here's a comprehensive approach:

1. **Daily Practices**:
   - Meditation or mindfulness
   - Regular exercise
   - Quality sleep
   - Social connections

2. **Emotional Wellbeing**:
   - Journaling
   - Creative expression
   - Nature connection
   - Gratitude practice

3. **Professional Support**:
   - Therapy options
   - Support groups
   - Crisis resources
   - Self-help tools

What specific aspect would you like to explore?"""

    def get_sleep_response(self, query):
        if 'insomnia' in query.lower():
            return """Let's improve your sleep! 😴

Here's a comprehensive guide for better sleep:

1. **Sleep Environment**:
   - Cool, dark, quiet room
   - Comfortable mattress
   - Blackout curtains
   - White noise if needed

2. **Bedtime Routine**:
   - Consistent sleep schedule
   - Relaxing activities
   - Limit screen time
   - Avoid stimulants

3. **Sleep Hygiene**:
   - No caffeine after 2 PM
   - Limit alcohol
   - Regular exercise
   - Light dinner

Would you like specific relaxation techniques or a detailed sleep schedule?"""
        else:
            return """Let's enhance your sleep quality! 🌙

Here's a practical sleep improvement guide:

1. **Sleep Schedule**:
   - Consistent bedtime
   - Regular wake time
   - 7-9 hours sleep
   - Weekend consistency

2. **Sleep Environment**:
   - Cool temperature (65-68°F)
   - Dark room
   - Quiet space
   - Comfortable bedding

3. **Pre-sleep Routine**:
   - Relaxing activities
   - No screens 1 hour before bed
   - Light reading
   - Warm bath/shower

What specific sleep challenges are you facing?"""

    def get_general_health_response(self, query):
        return """Let's focus on your overall wellbeing! 🌟

Here's a holistic approach to health:

1. **Physical Health**:
   - Regular exercise
   - Balanced diet
   - Adequate sleep
   - Regular check-ups

2. **Mental Wellbeing**:
   - Stress management
   - Social connections
   - Hobbies and interests
   - Professional support if needed

3. **Preventive Care**:
   - Regular screenings
   - Vaccinations
   - Dental care
   - Vision checks

4. **Lifestyle Factors**:
   - No smoking
   - Limited alcohol
   - Safe sun exposure
   - Regular physical activity

What specific aspect would you like to explore?"""

def main():
    chatbot = HealthChatbot()
    print("Health Assistant Chatbot (type 'quit' to exit)")
    print("=" * 50)
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("Health Assistant: Take care of your health! Goodbye!")
            break
        
        response = chatbot.get_response(user_input)
        print("\nHealth Assistant:", response)
        print("=" * 50)

if __name__ == "__main__":
    main() 