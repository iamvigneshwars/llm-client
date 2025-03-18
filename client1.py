import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

import markdown2  # For rendering Markdown to HTML
import requests
from tkhtmlview import HTMLScrolledText  # For displaying HTML in Tkinter


class RagClient(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RAG API Client")

        # Connection status
        self.connected = False
        self.status_label = tk.Label(self, text="Checking connection...", fg="orange")
        self.status_label.grid(row=0, column=0, columnspan=2, sticky="w")

        # GUI components
        self.question_label = tk.Label(self, text="Enter your question:")
        self.question_entry = tk.Entry(self, width=50)
        self.ask_button = tk.Button(self, text="Ask", command=self.on_ask)
        self.response_text = HTMLScrolledText(
            self, width=80, height=20
        )  # Using HTMLScrolledText for Markdown

        # Layout components
        self.question_label.grid(row=1, column=0, sticky="w")
        self.question_entry.grid(row=1, column=1)
        self.ask_button.grid(row=2, column=1, pady=5)
        self.response_text.grid(row=3, column=0, columnspan=2, pady=10)

        # Start connection check in background
        threading.Thread(target=self.check_connection, daemon=True).start()

    def check_connection(self):
        """Check connection to the server in the background."""
        try:
            response = requests.get("http://172.23.167.1:5000/health", timeout=5)
            response.raise_for_status()
            self.connected = True
            self.status_label.config(text="Connected to server", fg="green")
        except requests.exceptions.RequestException:
            self.connected = False
            self.status_label.config(text="Not connected to server", fg="red")

    def on_ask(self):
        """Handle the 'Ask' button click."""
        if not self.connected:
            messagebox.showerror("Error", "Not connected to the server")
            return

        question = self.question_entry.get().strip()
        if not question:
            messagebox.showwarning("Warning", "Please enter a question")
            return

        self.ask_button.config(text="Processing...", state=tk.DISABLED)
        self.response_text.set_html("")  # Clear previous response

        # Start a new thread for the API request
        thread = threading.Thread(target=self.make_request, args=(question,))
        thread.start()

    def make_request(self, question):
        """Send a POST request to the RAG API."""
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
        """Update the GUI with the API response."""

        def _update():
            if "error" in data:
                html_content = f"<p style='color:red'>Error: {data['error']}</p>"
            else:
                answer = data.get("answer", "")
                # Convert Markdown to HTML
                html_content = markdown2.markdown(answer)
            self.response_text.set_html(html_content)
            self.ask_button.config(text="Ask", state=tk.NORMAL)

        # Schedule the update on the main thread
        self.after(0, _update)


if __name__ == "__main__":
    app = RagClient()
    app.mainloop()
