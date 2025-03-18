import json
import os
import threading
from datetime import datetime

import customtkinter as ctk
import requests


class ModernChatbot(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Diamond Chatbot")
        self.geometry("1000x700")
        self.resizable(True, True)

        # Set appearance and enable high DPI scaling
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        ctk.deactivate_automatic_dpi_awareness()

        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Chat history storage
        self.history_file = "chatbot_logs.json"
        self.load_history()

        # Main frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Chat display
        self.chat_display = ctk.CTkTextbox(
            self.main_frame,
            wrap="word",
            font=("Roboto", 15),
            corner_radius=20,
            fg_color="#2B2B2B",
            text_color="#E0E0E0",
        )
        self.chat_display.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 10))
        self.chat_display.configure(state="disabled")

        # Input frame
        self.input_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.input_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=20)
        self.input_frame.grid_columnconfigure(0, weight=1)

        # Status label
        self.status_label = ctk.CTkLabel(
            self.input_frame,
            text="Checking connection...",
            font=("Roboto", 13, "bold"),
            text_color="#FFA726",
        )
        self.status_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        # Input field
        self.input_field = ctk.CTkTextbox(
            self.input_frame,
            height=88,
            font=("Roboto", 14),
            corner_radius=0,
            wrap="word",
        )
        self.input_field.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        self.input_field.bind("<Return>", self.on_send)
        self.input_field.bind("<Shift-Return>", lambda e: None)

        # Button frame for stacking Send and Copy Response
        self.button_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        self.button_frame.grid(row=1, column=1, sticky="ns")

        # Send button
        self.send_button = ctk.CTkButton(
            self.button_frame,
            text="Send",
            command=self.on_send,
            width=120,
            height=40,
            font=("Roboto", 14, "bold"),
            corner_radius=8,
            fg_color="#2ECC71",
            hover_color="#27AE60",
        )
        self.send_button.grid(row=0, column=0, pady=(0, 8))

        # Copy Response button
        self.copy_button = ctk.CTkButton(
            self.button_frame,
            text="Copy Response",
            command=self.copy_response,
            width=120,
            height=40,
            font=("Roboto", 14, "bold"),
            corner_radius=8,
        )
        self.copy_button.grid(row=1, column=0)

        # Connection status
        self.connected = False
        threading.Thread(target=self.check_connection, daemon=True).start()

    def load_history(self):
        if os.path.exists(self.history_file):
            with open(self.history_file, "r") as f:
                self.history = json.load(f)
        else:
            self.history = []

    def save_history(self, question, response):
        timestamp = datetime.now().isoformat()
        entry = {"timestamp": timestamp, "question": question, "response": response}
        self.history.append(entry)
        with open(self.history_file, "w") as f:
            json.dump(self.history, f, indent=2)

    def check_connection(self):
        try:
            response = requests.get("http://172.23.167.1:5000/health", timeout=5)
            response.raise_for_status()
            self.connected = True
            self.update_status("Connected", "#4CAF50")
        except requests.exceptions.RequestException:
            self.connected = False
            self.update_status("Disconnected", "#EF5350")

    def update_status(self, text, color):
        self.after(0, lambda: self.status_label.configure(text=text, text_color=color))

    def on_send(self, event=None):
        self.check_connection()
        if not self.connected:
            self.show_error("Not connected to the server")
            return

        question = self.input_field.get("1.0", "end-1c").strip()
        if not question:
            return

        self.send_button.configure(state="disabled", text="generating...")
        self.input_field.delete("1.0", "end")

        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.insert("end", f"You: {question}\n\n")
        self.chat_display.configure(state="disabled")

        threading.Thread(target=self.make_request, args=(question,)).start()

    def make_request(self, question):
        try:
            payload = {"question": question}
            response = requests.post(
                "http://172.23.167.1:5000/ask", json=payload, timeout=30
            )
            response.raise_for_status()
            data = response.json()
            self.connected = True
            self.update_status("Connected", "#4CAF50")
            self.update_response(data, question)
        except requests.exceptions.RequestException as e:
            self.connected = False
            self.update_status("Disconnected", "#EF5350")
            self.update_response({"error": str(e)}, question)

    def update_response(self, data, question):
        self.chat_display.configure(state="normal")

        if "error" in data:
            response_text = f"Error: {data['error']}"
            self.chat_display.insert("end", f"Bot: {response_text}", "error")
            self.chat_display.tag_config("error", foreground="#EF5350")
        else:
            answer = data.get("answer", "")
            plain_text = answer.replace("**", "").replace("*", "").replace("#", "")
            import re

            plain_text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1 (\2)", plain_text)
            self.chat_display.insert("end", f"Bot: {plain_text}")

        self.chat_display.configure(state="disabled")
        self.send_button.configure(state="normal", text="Send")

        response = data.get("answer", data.get("error", "Unknown error"))
        self.save_history(question, response)

    def show_error(self, message):
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.insert("end", f"Error: {message}", "error")
        self.chat_display.tag_config("error", foreground="#EF5350")
        self.chat_display.configure(state="disabled")

    def copy_response(self):
        # Get the full text from the chat display
        full_text = self.chat_display.get("1.0", "end-1c").strip()
        if not full_text:
            return

        # Extract only the Bot's response (everything after "Bot: ")
        bot_response = ""
        lines = full_text.split("\n")
        for line in lines:
            if line.startswith("Bot: "):
                bot_response = line[5:]  # Remove "Bot: " prefix
                break

        if bot_response:
            self.clipboard_clear()
            self.clipboard_append(bot_response)


if __name__ == "__main__":
    app = ModernChatbot()
    app.mainloop()
