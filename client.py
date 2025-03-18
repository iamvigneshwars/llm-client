import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

import markdown2
import requests


class RagClient(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Diamond Test Chatbot")
        self.geometry("900x650")
        self.configure(bg="#ECEFF1")  # Light blue-gray background

        # Make window resizable
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Modern color scheme
        self.bg_color = "#ECEFF1"
        self.accent_color = "#0288D1"  # Blue
        self.button_color = "#4CAF50"  # Green
        self.text_color = "#212121"

        # Top frame for status
        top_frame = tk.Frame(self, bg=self.bg_color)
        top_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        top_frame.grid_columnconfigure(0, weight=1)

        self.status_label = tk.Label(
            top_frame,
            text="Checking connection...",
            fg="#F57C00",  # Orange
            bg=self.bg_color,
            font=("Helvetica", 11, "bold"),
        )
        self.status_label.pack(side=tk.LEFT)

        # Input frame
        input_frame = tk.Frame(self, bg=self.bg_color)
        input_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        input_frame.grid_columnconfigure(1, weight=1)

        self.question_label = tk.Label(
            input_frame,
            text="Ask a Question:",
            bg=self.bg_color,
            fg=self.text_color,
            font=("Helvetica", 12, "bold"),
        )
        self.question_entry = tk.Entry(
            input_frame,
            font=("Helvetica", 11),
            bg="white",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#B0BEC5",
            highlightcolor=self.accent_color,
        )
        self.ask_button = tk.Button(
            input_frame,
            text="Ask",
            command=self.on_ask,
            bg=self.button_color,
            fg="white",
            font=("Helvetica", 11, "bold"),
            relief="flat",
            padx=15,
            pady=5,
            activebackground="#45A049",
            cursor="hand2",
        )

        self.question_label.grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.question_entry.grid(row=0, column=1, sticky="ew")
        self.ask_button.grid(row=0, column=2, padx=10)

        # Response frame
        response_frame = tk.Frame(self, bg=self.bg_color)
        response_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        response_frame.grid_columnconfigure(0, weight=1)
        response_frame.grid_rowconfigure(0, weight=1)

        self.response_text = scrolledtext.ScrolledText(
            response_frame,
            wrap=tk.WORD,
            font=("Helvetica", 11),
            bg="white",
            fg=self.text_color,
            relief="flat",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground="#B0BEC5",
            padx=10,
            pady=10,
        )
        self.response_text.grid(row=0, column=0, sticky="nsew")

        # Bottom frame for copy button
        bottom_frame = tk.Frame(self, bg=self.bg_color)
        bottom_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))

        self.copy_button = tk.Button(
            bottom_frame,
            text="Copy Response",
            command=self.copy_response,
            bg=self.accent_color,
            fg="white",
            font=("Helvetica", 10, "bold"),
            relief="flat",
            padx=10,
            pady=3,
            activebackground="#0277BD",
            cursor="hand2",
        )
        self.copy_button.pack(side=tk.RIGHT)

        # Start connection check
        threading.Thread(target=self.check_connection, daemon=True).start()

    def check_connection(self):
        try:
            response = requests.get("http://172.23.167.1:5000/health", timeout=5)
            response.raise_for_status()
            self.connected = True
            self.status_label.config(text="Connected to server", fg="#4CAF50")
        except requests.exceptions.RequestException:
            self.connected = False
            self.status_label.config(text="Not connected to server", fg="#D32F2F")

    def on_ask(self):
        if not self.connected:
            messagebox.showerror("Error", "Not connected to the server")
            return

        question = self.question_entry.get().strip()
        if not question:
            messagebox.showwarning("Warning", "Please enter a question")
            return

        self.ask_button.config(text="Generating answer...", state=tk.DISABLED)
        self.response_text.delete(1.0, tk.END)
        thread = threading.Thread(target=self.make_request, args=(question,))
        thread.start()

    def make_request(self, question):
        try:
            payload = {"question": question}
            response = requests.post(
                "http://172.23.167.1:5000/ask", json=payload, timeout=30
            )
            response.raise_for_status()
            data = response.json()
            self.update_response(data)
        except requests.exceptions.RequestException as e:
            self.update_response({"error": str(e)})

    def update_response(self, data):
        def _update():
            if "error" in data:
                response_text = f"Error: {data['error']}"
                self.response_text.insert(tk.END, response_text)
                self.response_text.tag_add("error", "1.0", "end")
                self.response_text.tag_config("error", foreground="#D32F2F")
            else:
                answer = data.get("answer", "")
                # Instead of stripping everything, preserve link URLs
                plain_text = answer.replace("**", "").replace("*", "").replace("#", "")
                # Replace Markdown links [text](URL) with "text (URL)"
                import re

                plain_text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1 (\2)", plain_text)
                self.response_text.insert(tk.END, plain_text)
            self.ask_button.config(text="Ask", state=tk.NORMAL)

        self.after(0, _update)

    def copy_response(self):
        text = self.response_text.get(1.0, tk.END).strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)


if __name__ == "__main__":
    app = RagClient()
    app.mainloop()
