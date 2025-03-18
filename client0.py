import json
import threading
import time  # Added missing import
import tkinter as tk
from tkinter import scrolledtext, ttk

import markdown
import requests
from tkinterweb import HtmlFrame


class SimpleRAGClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Diamond RAG Chat")
        self.root.geometry("800x600")
        self.root.minsize(650, 500)

        # Server configuration
        self.server_url = "http://172.23.167.1:5000"

        # Configure style
        style = ttk.Style()
        style.configure("TFrame", background="#f5f5f5")
        style.configure("TLabel", background="#f5f5f5", font=("Arial", 10))
        style.configure("Status.TLabel", foreground="blue", font=("Arial", 10, "bold"))
        style.configure("Error.TLabel", foreground="red", font=("Arial", 10, "bold"))

        # Create main container
        self.main_frame = ttk.Frame(root, style="TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Status area
        self.status_frame = ttk.Frame(self.main_frame, style="TFrame")
        self.status_frame.pack(fill=tk.X, padx=5, pady=5)

        self.status_label = ttk.Label(
            self.status_frame, text="Checking connection...", style="Status.TLabel"
        )
        self.status_label.pack(side=tk.LEFT, padx=5)

        # Create chat display area with HTML rendering support
        self.chat_frame = ttk.Frame(self.main_frame, style="TFrame")
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.chat_display = HtmlFrame(self.chat_frame)
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        # Initial HTML content
        self.chat_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                .message { margin-bottom: 20px; padding: 10px; border-radius: 10px; }
                .user { background-color: #e1f5fe; border-left: 4px solid #03a9f4; }
                .assistant { background-color: #f1f8e9; border-left: 4px solid #7cb342; }
                .system { background-color: #fffde7; border-left: 4px solid #fbc02d; }
                .sender { font-weight: bold; margin-bottom: 5px; }
                .content { line-height: 1.5; }
                code { background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px; }
                pre { background-color: #f0f0f0; padding: 10px; border-radius: 5px; overflow-x: auto; }
            </style>
        </head>
        <body>
            <div class="message system">
                <div class="sender">System</div>
                <div class="content">Checking connection to server...</div>
            </div>
        </body>
        </html>
        """

        self.chat_display.load_html(self.chat_html)

        # Create input area
        self.input_frame = ttk.Frame(self.main_frame, style="TFrame")
        self.input_frame.pack(fill=tk.X, padx=5, pady=5)

        self.user_input = scrolledtext.ScrolledText(
            self.input_frame, wrap=tk.WORD, height=3, bg="white"
        )
        self.user_input.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=5, pady=5)
        self.user_input.bind("<Return>", self.send_on_enter)

        self.send_button = ttk.Button(
            self.input_frame, text="Send", command=self.send_question
        )
        self.send_button.pack(side=tk.RIGHT, padx=5, pady=5)

        # Check the connection as soon as the app starts
        self.check_connection()

    def check_connection(self):
        """Check connection to the RAG API server"""

        def check():
            try:
                response = requests.get(f"{self.server_url}/status", timeout=5)

                if response.status_code == 200:
                    data = response.json()
                    pdf_name = data.get("pdf", "Unknown")
                    self.root.after(
                        0,
                        lambda: self.status_label.config(
                            text=f"Connected | PDF: {pdf_name}", style="Status.TLabel"
                        ),
                    )
                    self.root.after(
                        0,
                        lambda: self.add_message(
                            "System",
                            f"Connected to RAG server! Using document: {pdf_name}. Ask questions about the document.",
                        ),
                    )
                else:
                    self.root.after(
                        0,
                        lambda: self.status_label.config(
                            text="Connection Error", style="Error.TLabel"
                        ),
                    )
                    self.root.after(
                        0,
                        lambda: self.add_message(
                            "System",
                            f"Failed to connect to server: {response.status_code}",
                        ),
                    )
            except Exception as e:
                self.root.after(
                    0,
                    lambda: self.status_label.config(
                        text="Connection Error", style="Error.TLabel"
                    ),
                )
                self.root.after(
                    0,
                    lambda: self.add_message(
                        "System", f"Failed to connect to server: {str(e)}"
                    ),
                )

        threading.Thread(target=check).start()

    def add_message(self, sender, message, message_type="system"):
        """Add a message to the chat display using HTML"""
        # Convert message to HTML if needed
        if message_type == "assistant":
            # Convert markdown to HTML
            message_html = markdown.markdown(
                message, extensions=["extra", "codehilite"]
            )
        else:
            # Escape HTML special characters for regular text
            message_html = message.replace("<", "&lt;").replace(">", "&gt;")
            message_html = message_html.replace("\n", "<br>")

        # Create a new message div
        new_message = f"""
            <div class="message {message_type}">
                <div class="sender">{sender}</div>
                <div class="content">{message_html}</div>
            </div>
        """

        # Update the HTML content
        self.chat_html = self.chat_html.replace("</body>", f"{new_message}\n</body>")
        self.chat_display.load_html(self.chat_html)

        # Fixed: Correct way to execute JavaScript in tkinterweb
        self.chat_display.evaluate_js(
            """
            document.body.scrollTop = document.body.scrollHeight;
            document.documentElement.scrollTop = document.documentElement.scrollHeight;
            """
        )

    def send_on_enter(self, event):
        """Handle Enter key to send message"""
        # Only send if not pressing shift+enter for new line
        if not event.state & 0x1:  # 0x1 is the mask for Shift
            self.send_question()
            return "break"  # Prevents the default behavior (new line)
        return None  # Allows default behavior (new line with shift+enter)

    def send_question(self):
        """Send the user question to the RAG API"""
        question = self.user_input.get("1.0", tk.END).strip()
        if not question:
            return

        # Add user message to chat
        self.add_message("You", question, "user")

        # Clear input field
        self.user_input.delete("1.0", tk.END)

        # Disable send button during processing
        self.send_button.config(state=tk.DISABLED)

        # Add a "thinking" message
        thinking_id = f"thinking_{int(time.time())}"
        self.add_message("RAG Assistant", "Thinking...", "system")

        def query_api():
            try:
                response = requests.post(
                    f"{self.server_url}/ask",
                    json={"question": question},
                    timeout=60,  # Longer timeout for LLM processing
                )

                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "No answer provided")
                    processing_time = data.get("processing_time", "unknown")

                    # Remove the thinking message by rebuilding the HTML without it
                    self.chat_html = self.chat_html.replace(
                        f'<div class="message system">\n                <div class="sender">RAG Assistant</div>\n                <div class="content">Thinking...</div>\n            </div>',
                        "",
                    )

                    # Add the answer
                    self.root.after(
                        0,
                        lambda: self.add_message("RAG Assistant", answer, "assistant"),
                    )

                    # Add processing time as small text
                    self.root.after(
                        0,
                        lambda: self.add_message(
                            "System", f"Processing time: {processing_time} seconds"
                        ),
                    )
                else:
                    error_msg = f"Error: Received status code {response.status_code} from server"

                    # Remove the thinking message
                    self.chat_html = self.chat_html.replace(
                        f'<div class="message system">\n                <div class="sender">RAG Assistant</div>\n                <div class="content">Thinking...</div>\n            </div>',
                        "",
                    )

                    self.root.after(0, lambda: self.add_message("System", error_msg))
            except Exception as e:
                error_msg = f"Error querying RAG API: {str(e)}"

                # Remove the thinking message
                self.chat_html = self.chat_html.replace(
                    f'<div class="message system">\n                <div class="sender">RAG Assistant</div>\n                <div class="content">Thinking...</div>\n            </div>',
                    "",
                )

                self.root.after(0, lambda: self.add_message("System", error_msg))
            finally:
                self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL))

        # Run the API query in a separate thread to keep UI responsive
        threading.Thread(target=query_api).start()


def main():
    root = tk.Tk()
    app = SimpleRAGClient(root)
    root.mainloop()


if __name__ == "__main__":
    main()
