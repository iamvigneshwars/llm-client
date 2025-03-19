import json
import os
import threading
import re
from datetime import datetime
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import requests
from PIL import Image, ImageTk

class ModernChatbotUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.message_widgets = []
        self.message_count = 0  # Add message counter
        self.title("Diamond Chatbot")
        self.geometry("1100x800")
        self.minsize(800, 600)
        
        # Set appearance and enable high DPI scaling
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")
        ctk.deactivate_automatic_dpi_awareness()
        
        # Color scheme
        self.colors = {
            "bg_dark": "#1E1E2E",
            "bg_medium": "#282839",
            "accent": "#7B68EE",
            "accent_hover": "#6A5ACD",
            "text_light": "#F8F8F2",
            "text_muted": "#A6ADC8",
            "success": "#50FA7B",
            "error": "#FF5555",
            "warning": "#FFB86C",
            "user_message_bg": "#313244",
            "bot_message_bg": "#45475A"
        }
        
        # Configure grid
        self.grid_columnconfigure(0, weight=0)  # Sidebar
        self.grid_columnconfigure(1, weight=1)  # Chat area
        self.grid_rowconfigure(0, weight=1)
        
        # Chat history storage
        self.history_file = "chatbot_logs.json"
        self.load_history()
        self.current_history_index = -1
        
        # Create UI components
        self.create_sidebar()
        self.create_chat_area()
        
        # Connection status
        self.connected = False
        threading.Thread(target=self.check_connection, daemon=True).start()
        
        # Keyboard shortcuts
        self.bind("<Control-l>", lambda e: self.clear_chat())
        
    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r") as f:
                    self.history = json.load(f)
            except json.JSONDecodeError:
                self.history = []
        else:
            self.history = []
    
    def save_history(self, question, response):
        timestamp = datetime.now().isoformat()
        entry = {"timestamp": timestamp, "question": question, "response": response}
        self.history.append(entry)
        with open(self.history_file, "w") as f:
            json.dump(self.history, f, indent=2)
            
    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, corner_radius=0, fg_color=self.colors["bg_medium"], width=250)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)
        
        self.logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.logo_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        self.logo_label = ctk.CTkLabel(
            self.logo_frame, 
            text="Diamond", 
            font=("Roboto", 24, "bold"),
            text_color=self.colors["accent"]
        )
        self.logo_label.grid(row=0, column=0, sticky="w")
        
        self.logo_subtitle = ctk.CTkLabel(
            self.logo_frame,
            text="AI Assistant",
            font=("Roboto", 14),
            text_color=self.colors["text_muted"]
        )
        self.logo_subtitle.grid(row=1, column=0, sticky="w")
        
        self.history_label = ctk.CTkLabel(
            self.sidebar,
            text="Chat History",
            font=("Roboto", 16, "bold"),
            text_color=self.colors["text_light"]
        )
        self.history_label.grid(row=1, column=0, sticky="w", padx=20, pady=(20, 10))
        
        self.history_frame = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color="transparent",
            corner_radius=0
        )
        self.history_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.sidebar.grid_rowconfigure(2, weight=1)
        
        self.update_history_list()
        
        self.action_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.action_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=20)
        self.action_frame.grid_columnconfigure(0, weight=1)
        self.action_frame.grid_columnconfigure(1, weight=1)
        
        self.clear_btn = ctk.CTkButton(
            self.action_frame,
            text="Clear Chat",
            command=self.clear_chat,
            font=("Roboto", 13),
            fg_color=self.colors["bg_dark"],
            hover_color=self.colors["bg_medium"],
            corner_radius=8
        )
        self.clear_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        self.theme_btn = ctk.CTkButton(
            self.action_frame,
            text="Toggle Theme",
            command=self.toggle_theme,
            font=("Roboto", 13),
            fg_color=self.colors["bg_dark"],
            hover_color=self.colors["bg_medium"],
            corner_radius=8
        )
        self.theme_btn.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        
        self.status_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.status_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 20))
        
        self.status_indicator = ctk.CTkLabel(
            self.status_frame,
            text="●",
            font=("Roboto", 20),
            text_color=self.colors["warning"]
        )
        self.status_indicator.grid(row=0, column=0, padx=(0, 5))
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Checking connection...",
            font=("Roboto", 13),
            text_color=self.colors["text_muted"]
        )
        self.status_label.grid(row=0, column=1, sticky="w")
        
    def create_chat_area(self):
        self.chat_area = ctk.CTkFrame(self, corner_radius=0, fg_color=self.colors["bg_dark"])
        self.chat_area.grid(row=0, column=1, sticky="nsew")
        self.chat_area.grid_columnconfigure(0, weight=1)
        self.chat_area.grid_rowconfigure(0, weight=1)
        
        self.messages_frame = ctk.CTkScrollableFrame(
            self.chat_area,
            fg_color="transparent",
            corner_radius=0
        )
        self.messages_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.messages_frame.grid_columnconfigure(0, weight=1)
        
        self.add_bot_message("Hello! I'm Diamond, your AI assistant. How can I help you today?")
        
        self.input_area = ctk.CTkFrame(self.chat_area, fg_color="transparent")
        self.input_area.grid(row=1, column=0, sticky="ew", padx=20, pady=20)
        self.input_area.grid_columnconfigure(0, weight=1)
        
        self.input_container = ctk.CTkFrame(
            self.input_area,
            fg_color=self.colors["bg_medium"],
            corner_radius=10
        )
        self.input_container.grid(row=0, column=0, sticky="ew")
        self.input_container.grid_columnconfigure(0, weight=1)
        
        self.input_field = ctk.CTkTextbox(
            self.input_container,
            height=100,
            font=("Roboto", 14),
            fg_color="transparent",
            border_width=0,
            wrap="word"
        )
        self.input_field.grid(row=0, column=0, sticky="ew", padx=15, pady=10)
        self.input_field.bind("<Return>", self.on_send)
        self.input_field.bind("<Shift-Return>", lambda e: None)
        self.input_field.bind("<Control-a>", self.select_all_text)
        self.input_field.bind("<Up>", self.navigate_history_up)
        self.input_field.bind("<Down>", self.navigate_history_down)
        
        self.buttons_frame = ctk.CTkFrame(self.input_container, fg_color="transparent")
        self.buttons_frame.grid(row=0, column=1, sticky="nse", padx=(0, 10), pady=10)
        
        self.copy_button = ctk.CTkButton(
            self.buttons_frame,
            text="Copy",
            command=self.copy_response,
            width=80,
            height=35,
            font=("Roboto", 13),
            fg_color=self.colors["bg_dark"],
            hover_color="#3A3A5E",
            corner_radius=8
        )
        self.copy_button.grid(row=0, column=0, padx=5)
        
        self.send_button = ctk.CTkButton(
            self.buttons_frame,
            text="Send",
            command=self.on_send,
            width=80,
            height=35,
            font=("Roboto", 13, "bold"),
            fg_color=self.colors["accent"],
            hover_color=self.colors["accent_hover"],
            corner_radius=8
        )
        self.send_button.grid(row=0, column=1, padx=5)
        
        self.after(100, lambda: self.input_field.focus())
        
    def add_user_message(self, text):
        message_frame = ctk.CTkFrame(
            self.messages_frame,
            fg_color=self.colors["user_message_bg"],
            corner_radius=10
        )
        message_frame.grid(row=self.message_count, column=0, sticky="e", pady=(0, 15), padx=(80, 0))
        
        user_label = ctk.CTkLabel(
            message_frame,
            text="You",
            font=("Roboto", 12, "bold"),
            text_color=self.colors["accent"]
        )
        user_label.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 0))
        
        message_label = ctk.CTkLabel(
            message_frame,
            text=text,
            font=("Roboto", 14),
            text_color=self.colors["text_light"],
            justify="left",
            wraplength=600
        )
        message_label.grid(row=1, column=0, sticky="w", padx=15, pady=(5, 10))
        
        self.message_count += 1
        self.after(100, self.scroll_to_bottom)
        
    def add_bot_message(self, text):
        message_frame = ctk.CTkFrame(
            self.messages_frame,
            fg_color=self.colors["bot_message_bg"],
            corner_radius=10
        )
        message_frame.grid(row=self.message_count, column=0, sticky="w", pady=(0, 15), padx=(0, 80))
        
        bot_label = ctk.CTkLabel(
            message_frame,
            text="Diamond",
            font=("Roboto", 12, "bold"),
            text_color=self.colors["accent"]
        )
        bot_label.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 0))
        
        message_label = ctk.CTkLabel(
            message_frame,
            text=text,
            font=("Roboto", 14),
            text_color=self.colors["text_light"],
            justify="left",
            wraplength=600
        )
        message_label.grid(row=1, column=0, sticky="w", padx=15, pady=(5, 10))
        
        self.latest_bot_message = text
        self.message_widgets.append(message_frame)
        self.message_count += 1
        self.after(100, self.scroll_to_bottom)
        
    def add_error_message(self, text):
        message_frame = ctk.CTkFrame(
            self.messages_frame,
            fg_color=self.colors["bot_message_bg"],
            corner_radius=10
        )
        message_frame.grid(row=self.message_count, column=0, sticky="w", pady=(0, 15), padx=(0, 80))
        
        bot_label = ctk.CTkLabel(
            message_frame,
            text="Error",
            font=("Roboto", 12, "bold"),
            text_color=self.colors["error"]
        )
        bot_label.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 0))
        
        message_label = ctk.CTkLabel(
            message_frame,
            text=text,
            font=("Roboto", 14),
            text_color=self.colors["error"],
            justify="left",
            wraplength=600
        )
        message_label.grid(row=1, column=0, sticky="w", padx=15, pady=(5, 10))
        
        self.message_count += 1
        self.after(100, self.scroll_to_bottom)
        
    def scroll_to_bottom(self):
        self.messages_frame._parent_canvas.yview_moveto(1.0)
        
    def on_send(self, event=None):
        if event and event.state & 0x4:
            return
            
        self.check_connection()
        if not self.connected:
            self.add_error_message("Not connected to the server")
            return

        question = self.input_field.get("1.0", "end-1c").strip()
        if not question:
            return

        self.send_button.configure(state="disabled", text="...")
        self.input_field.delete("1.0", "end")
        
        self.add_user_message(question)
        
        threading.Thread(target=self.make_request, args=(question,)).start()
        
    def make_request(self, question):
        try:
            payload = {"question": question}
            response = requests.post(
                "http://172.23.162.4:5000/ask", json=payload, timeout=30
            )
            response.raise_for_status()
            data = response.json()
            self.connected = True
            self.update_status("Connected", self.colors["success"])
            self.update_response(data, question)
        except requests.exceptions.RequestException as e:
            self.connected = False
            self.update_status("Disconnected", self.colors["error"])
            self.add_error_message(f"Connection error: {str(e)}")
            self.after(0, lambda: self.send_button.configure(state="normal", text="Send"))

    def process_markdown(self, text):
        def replace_link(match):
            link_text = match.group(1)
            link_url = match.group(2)
            return f"{link_text} ({link_url})"
        
        link_pattern = r'\[(.*?)\]\(((?:[^()]*|\([^()]*\))*)\)'
        processed_text = re.sub(link_pattern, replace_link, text)
        
        processed_text = processed_text.replace("**", "").replace("*", "")
        
        processed_text = re.sub(r'^#+\s+', '', processed_text, flags=re.MULTILINE)
        
        return processed_text

    def update_response(self, data, question):
        if "error" in data:
            error_text = f"Error: {data['error']}"
            self.add_error_message(error_text)
        else:
            answer = data.get("answer", "")
            plain_text = self.process_markdown(answer)
            self.add_bot_message(plain_text)
            self.latest_bot_message = plain_text

        self.send_button.configure(state="normal", text="Send")

        response = data.get("answer", data.get("error", "Unknown error"))
        self.save_history(question, response)
        self.update_history_list()
        
    def check_connection(self):
        try:
            response = requests.get("http://172.23.162.4:5000/health", timeout=5)
            response.raise_for_status()
            self.connected = True
            self.update_status("Connected", self.colors["success"])
        except requests.exceptions.RequestException:
            self.connected = False
            self.update_status("Disconnected", self.colors["error"])

    def update_status(self, text, color):
        self.after(0, lambda: self.status_indicator.configure(text_color=color))
        self.after(0, lambda: self.status_label.configure(text=text))
        
    def copy_response(self):
        if hasattr(self, 'latest_bot_message') and self.latest_bot_message:
            self.clipboard_clear()
            self.clipboard_append(self.latest_bot_message)
            
            original_color = self.copy_button.cget("fg_color")
            self.copy_button.configure(fg_color=self.colors["success"], text="Copied!")
            self.after(1000, lambda: self.copy_button.configure(fg_color=original_color, text="Copy"))
            
    def select_all_text(self, event):
        event.widget.tag_add("sel", "1.0", "end")
        return "break"
        
    def clear_chat(self, event=None):
        for widget in self.messages_frame.winfo_children():
            widget.destroy()
        self.message_count = 0
        self.add_bot_message("Chat cleared! How can I help you today?")
        
    def toggle_theme(self):
        current_mode = ctk.get_appearance_mode()
        new_mode = "Dark" if current_mode == "Light" else "Light"
        ctk.set_appearance_mode(new_mode)
        
    def update_history_list(self):
        for widget in self.history_frame.winfo_children():
            widget.destroy()
            
        for i, entry in enumerate(reversed(self.history[-10:])):
            timestamp = datetime.fromisoformat(entry["timestamp"])
            formatted_time = timestamp.strftime("%H:%M:%S")
            formatted_date = timestamp.strftime("%b %d")
            
            question = entry["question"]
            if len(question) > 30:
                question = question[:27] + "..."
                
            history_item = ctk.CTkButton(
                self.history_frame,
                text=f"{formatted_time} - {question}",
                font=("Roboto", 12),
                anchor="w",
                fg_color="transparent",
                text_color=self.colors["text_muted"],
                hover_color=self.colors["bg_dark"],
                corner_radius=5,
                height=30,
                command=lambda q=entry["question"], r=entry["response"]: self.load_history_item(q, r)
            )
            history_item.grid(row=i, column=0, sticky="ew", pady=(0, 5))
            
    def load_history_item(self, question, response):
        for widget in self.messages_frame.winfo_children():
            widget.destroy()
        self.message_count = 0
            
        self.add_user_message(question)
        plain_text = self.process_markdown(response)
        self.add_bot_message(plain_text)
        
    def navigate_history_up(self, event=None):
        if not self.history:
            return "break"
            
        if self.current_history_index < len(self.history) - 1:
            self.current_history_index += 1
            self.input_field.delete("1.0", "end")
            self.input_field.insert("1.0", self.history[-(self.current_history_index+1)]["question"])
        return "break"
        
    def navigate_history_down(self, event=None):
        if self.current_history_index > -1:
            self.current_history_index -= 1
            self.input_field.delete("1.0", "end")
            if self.current_history_index >= 0:
                self.input_field.insert("1.0", self.history[-(self.current_history_index+1)]["question"])
        return "break"

if __name__ == "__main__":
    app = ModernChatbotUI()
    app.mainloop()
