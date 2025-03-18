import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

import requests


class RagClient(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RAG API Client")

        # Create GUI components
        self.question_label = tk.Label(self, text="Enter your question:")
        self.question_entry = tk.Entry(self, width=50)
        self.debug_var = tk.BooleanVar()
        self.debug_check = tk.Checkbutton(
            self, text="Show sources", variable=self.debug_var
        )
        self.ask_button = tk.Button(self, text="Ask", command=self.on_ask)
        self.response_text = scrolledtext.ScrolledText(
            self, width=80, height=20, wrap=tk.WORD
        )
        self.response_text.config(state=tk.DISABLED)

        # Layout components
        self.question_label.grid(row=0, column=0, sticky="w")
        self.question_entry.grid(row=0, column=1, columnspan=2)
        self.debug_check.grid(row=1, column=0, columnspan=2, sticky="w")
        self.ask_button.grid(row=1, column=2)
        self.response_text.grid(row=2, column=0, columnspan=3, pady=10)

    def on_ask(self):
        """Handle the 'Ask' button click."""
        question = self.question_entry.get().strip()
        if not question:
            messagebox.showwarning("Warning", "Please enter a question")
            return
        debug = self.debug_var.get()

        # Disable button and show processing state
        self.ask_button.config(text="Processing...", state=tk.DISABLED)
        self.response_text.config(state=tk.NORMAL)
        self.response_text.delete(1.0, tk.END)
        self.response_text.config(state=tk.DISABLED)

        # Start a new thread for the API request
        thread = threading.Thread(target=self.make_request, args=(question, debug))
        thread.start()

    def make_request(self, question, debug):
        """Send a POST request to the RAG API."""
        try:
            payload = {"question": question, "debug": debug}
            response = requests.post(
                "http://172.23.167.1:5000/ask", json=payload, timeout=30
            )
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()
            self.update_response(data)
        except requests.exceptions.RequestException as e:
            self.update_response({"error": str(e)})

    def update_response(self, data):
        """Update the GUI with the API response."""

        def _update():
            self.response_text.config(state=tk.NORMAL)
            self.response_text.delete(1.0, tk.END)
            if "error" in data:
                self.response_text.insert(tk.END, f"Error: {data['error']}\n")
            else:
                answer = data.get("answer", "")
                self.response_text.insert(tk.END, "Answer:\n")
                self.response_text.insert(tk.END, answer + "\n\n")
                if "sources" in data and data["sources"]:
                    self.response_text.insert(tk.END, "Sources:\n")
                    for source in data["sources"]:
                        page = source.get("page", "unknown")
                        excerpt = source.get("excerpt", "")
                        self.response_text.insert(tk.END, f"Page {page}: {excerpt}\n")
            self.response_text.config(state=tk.DISABLED)
            self.ask_button.config(text="Ask", state=tk.NORMAL)

        # Schedule the update on the main thread
        self.after(0, _update)


if __name__ == "__main__":
    app = RagClient()
    app.mainloop()
