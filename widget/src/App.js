import React, { useState, useEffect, useRef } from 'react';
import { sendMessage } from './api';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { text: input, isBot: false };
    setMessages(prev => [...prev, userMessage]);
    setInput('');

    const botReply = await sendMessage(input);
    setMessages(prev => [...prev, { text: botReply, isBot: true }]);
  };

  return (
    <div className="chatbot-widget">
      {/* Toggle Button */}
      <div className="chat-toggle" onClick={() => setIsOpen(!isOpen)}>
        {isOpen ? "×" : "💬"}
      </div>

      {/* Chat Window */}
      {isOpen && (
        <div className="chat-window">
          <div className="chat-header">
            <h4>AI Assistant</h4>
            <span onClick={() => setIsOpen(false)}>×</span>
          </div>
          <div className="chat-messages">
            {messages.length === 0 && (
              <p className="chat-placeholder">How can I help you today?</p>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`message-bubble ${m.isBot ? 'bot' : 'user'}`}>
                {m.text}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
          <div className="chat-footer">
            <input 
              value={input} 
              onChange={(e) => setInput(e.target.value)} 
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask anything..."
            />
            <button onClick={handleSend}>Send</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
