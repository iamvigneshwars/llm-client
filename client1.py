import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

import markdown2
import requests


class RagClient(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RAG API Client")
        self.geometry("800x600")
        self.configure(bg="#f0f0f0")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # Connection status
        self.connected = False
        self.status_label = tk.Label(
            self,
            text="Checking connection...",
            fg="orange",
            bg="#f0f0f0",
            font=("Arial", 10),
        )
        self.status_label.grid(
            row=0, column=0, columnspan=2, sticky="w", padx=10, pady=5
        )

        # Input frame
        input_frame = tk.Frame(self, bg="#f0f0f0")
        input_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        input_frame.grid_columnconfigure(1, weight=1)

        # Question input
        self.question_label = tk.Label(
            input_frame, text="Enter your question:", bg="#f0f0f0", font=("Arial", 11)
        )
        self.question_entry = tk.Entry(input_frame, font=("Arial", 11))
        self.ask_button = tk.Button(
            input_frame,
            text="Ask",
            command=self.on_ask,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=10,
        )

        self.question_label.grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.question_entry.grid(row=0, column=1, sticky="ew")
        self.ask_button.grid(row=0, column=2, padx=5)

        # Response area
        response_frame = tk.Frame(self, bg="#f0f0f0")
        response_frame.grid(
            row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=10
        )
        response_frame.grid_columnconfigure(0, weight=1)
        response_frame.grid_rowconfigure(0, weight=1)

        self.response_text = scrolledtext.ScrolledText(
            response_frame,
            wrap=tk.WORD,
            font=("Arial", 11),
            bg="white",
            relief="sunken",
            borderwidth=2,
        )
        self.response_text.grid(row=0, column=0, sticky="nsew")

        self.copy_button = tk.Button(
            response_frame,
            text="Copy Response",
            command=self.copy_response,
            bg="#2196F3",
            fg="white",
            font=("Arial", 10),
            relief="flat",
        )
        self.copy_button.grid(row=1, column=0, sticky="e", pady=5)

        threading.Thread(target=self.check_connection, daemon=True).start()

    def check_connection(self):
        try:
            response = requests.get("http://172.23.167.1:5000/health", timeout=5)
            response.raise_for_status()
            self.connected = True
            self.status_label.config(text="Connected to server", fg="green")
        except requests.exceptions.RequestException:
            self.connected = False
            self.status_label.config(text="Not connected to server", fg="red")

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
                self.response_text.tag_config("error", foreground="red")
            else:
                answer = data.get("answer", "")
                plain_text = answer.replace("**", "").replace("*", "").replace("#", "")
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
