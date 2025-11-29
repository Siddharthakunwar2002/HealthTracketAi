import tkinter as tk
from tkinter import scrolledtext, ttk
from chatbot import HealthChatbot
import threading

class HealthChatbotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Health Assistant Chatbot")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")
        
        # Initialize chatbot
        self.chatbot = HealthChatbot()
        
        # Create main frame
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create chat display
        self.chat_display = scrolledtext.ScrolledText(
            self.main_frame,
            wrap=tk.WORD,
            width=70,
            height=30,
            font=("Arial", 10),
            bg="#ffffff"
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.chat_display.config(state=tk.DISABLED)
        
        # Create input frame
        self.input_frame = ttk.Frame(self.main_frame)
        self.input_frame.pack(fill=tk.X)
        
        # Create input field
        self.input_field = ttk.Entry(
            self.input_frame,
            font=("Arial", 10)
        )
        self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.input_field.bind("<Return>", self.send_message)
        
        # Create send button
        self.send_button = ttk.Button(
            self.input_frame,
            text="Send",
            command=self.send_message
        )
        self.send_button.pack(side=tk.RIGHT)
        
        # Add welcome message
        self.add_message("Health Assistant", "Hello! I'm your health assistant. How can I help you today?")
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure("TButton", padding=5)
        self.style.configure("TEntry", padding=5)
        
    def add_message(self, sender, message):
        self.chat_display.config(state=tk.NORMAL)
        if sender == "You":
            self.chat_display.insert(tk.END, f"{sender}: ", "user")
        else:
            self.chat_display.insert(tk.END, f"{sender}: ", "bot")
        
        self.chat_display.insert(tk.END, f"{message}\n\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        # Configure tags for different message styles
        self.chat_display.tag_config("user", foreground="#007bff")
        self.chat_display.tag_config("bot", foreground="#28a745")
    
    def send_message(self, event=None):
        message = self.input_field.get().strip()
        if message:
            # Clear input field
            self.input_field.delete(0, tk.END)
            
            # Add user message to chat
            self.add_message("You", message)
            
            # Get and display bot response
            def get_response():
                response = self.chatbot.get_response(message)
                self.add_message("Health Assistant", response)
            
            # Run response generation in a separate thread
            threading.Thread(target=get_response, daemon=True).start()

def main():
    root = tk.Tk()
    app = HealthChatbotGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 