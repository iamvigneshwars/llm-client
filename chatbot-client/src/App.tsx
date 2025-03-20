import React, { useState, useEffect, useRef } from 'react';
import './App.css';

interface ApiResponse {
    answer?: string;
    error?: string;
    metadata?: string;
}

const HOST = "172.23.162.4";

const App: React.FC = () => {
    const [input, setInput] = useState<string>('');
    const [isConnected, setIsConnected] = useState<boolean>(false);
    const [connectionStatus, setConnectionStatus] = useState<string>('Checking connection...');
    const [statusColor, setStatusColor] = useState<string>('#FFA726');
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [chatContent, setChatContent] = useState<string>('');
    const chatDisplayRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        checkConnection();

        if (inputRef.current) {
            inputRef.current.focus();
        }
    }, []);

    useEffect(() => {
        if (chatDisplayRef.current) {
            chatDisplayRef.current.scrollTop = chatDisplayRef.current.scrollHeight;
        }
    }, [chatContent]);

    const checkConnection = async () => {
        try {
            const response = await fetch(`http://${HOST}:5000/health`, {
                method: 'GET',
            });

            if (response.ok) {
                setIsConnected(true);
                updateStatus('Connected', '#4CAF50');
            } else {
                throw new Error('Server returned error status');
            }
        } catch (error) {
            setIsConnected(false);
            updateStatus('Disconnected', '#EF5350');
            console.error('Connection error:', error);
        }
    };

    const updateStatus = (text: string, color: string) => {
        setConnectionStatus(text);
        setStatusColor(color);
    };

    const saveHistory = (question: string, response: string, metadata: string) => {
        try {
            const timestamp = new Date().toISOString();
            const entry = { timestamp, question, response, metadata };

            // Get existing logs or initialize empty array
            const chatLogsString = localStorage.getItem('chatbot_logs');
            let chatLogs = chatLogsString ? JSON.parse(chatLogsString) : [];

            // Add new entry
            chatLogs.push(entry);

            // Save back to localStorage
            localStorage.setItem('chatbot_logs', JSON.stringify(chatLogs, null, 2));

            console.log('Chat log saved:', entry);
        } catch (error) {
            console.error('Error saving chat log:', error);
        }
    };

    const processMarkdown = (text: string): string => {
        // Replace markdown links
        const linkPattern = /\[(.*?)\]\(((?:[^()]*|\([^()]*\))*)\)/g;
        let processed = text.replace(linkPattern, (_, linkText, linkUrl) => `${linkText} (${linkUrl})`);

        // Remove bold and italic markers
        processed = processed.replace(/\*\*/g, '').replace(/\*/g, '');

        // Remove headings
        processed = processed.replace(/^#+\s+/gm, '');

        return processed;
    };

    const handleSend = async (event?: React.KeyboardEvent) => {
        // Handle Enter key (without shift)
        if (event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
            } else {
                return;
            }
        }

        await checkConnection();
        if (!isConnected) {
            showError('Not connected to the server');
            return;
        }

        const question = input.trim();
        if (!question) return;

        setInput('');
        setIsLoading(true);

        // Clear chat display and show user's question
        setChatContent(`You: ${question}\n\n`);

        try {
            const response = await fetch(`http://${HOST}:5000/ask`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ question })
            });

            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }

            const data: ApiResponse = await response.json();
            setIsConnected(true);
            updateStatus('Connected', '#4CAF50');

            if (data.error) {
                showError(data.error);
                saveHistory(question, data.error, 'Error');
            } else if (data.answer) {
                const plainText = processMarkdown(data.answer);
                setChatContent(prevContent => prevContent + `Bot: ${plainText}`);
                saveHistory(question, data.answer, data.metadata || 'Unknown metadata');
            }
        } catch (error) {
            setIsConnected(false);
            updateStatus('Disconnected', '#EF5350');
            const errorMsg = error instanceof Error ? error.message : 'Unknown error';
            showError(errorMsg);
            saveHistory(question, errorMsg, 'Connection Error');
        } finally {
            setIsLoading(false);
        }
    };

    const showError = (message: string) => {
        setChatContent(`Error: ${message}`);
    };

    const copyResponse = () => {
        if (!chatContent) return;

        let botResponse = '';
        let botPart = false;

        const lines = chatContent.split('\n');
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            if (line.startsWith('Bot: ')) {
                botPart = true;
                botResponse = line.substring(5);
                continue;
            }
            if (botPart && i > 0) {
                botResponse += '\n' + line;
            }
        }

        if (botResponse) {
            navigator.clipboard.writeText(botResponse)
                .then(() => {
                    console.log('Response copied to clipboard');
                })
                .catch(err => {
                    console.error('Failed to copy: ', err);
                });
        }
    };

    return (
        <div className="app-container">
            <div className="main-frame">
                <div
                    className="chat-display"
                    ref={chatDisplayRef}
                    dangerouslySetInnerHTML={{ __html: chatContent.replace(/\n/g, '<br/>') }}
                />

                <div className="input-frame">
                    <div className="status-label" style={{ color: statusColor }}>
                        {connectionStatus}
                    </div>

                    <div className="input-container">
                        <textarea
                            ref={inputRef}
                            className="input-field"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend(e)}
                            placeholder="ask me anything..."
                            disabled={isLoading}
                        />

                        <div className="button-frame">
                            <button
                                className="send-button"
                                onClick={() => handleSend()}
                                disabled={isLoading}
                            >
                                {isLoading ? 'generating...' : 'Send'}
                            </button>

                            <button
                                className="copy-button"
                                onClick={copyResponse}
                            >
                                Copy
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default App;
