import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  const simulateFacebookMessage = async () => {
    if (!input) return;
    
    // Add user message to UI
    const userMessage = { text: input, isBot: false };
    setMessages(prev => [...prev, userMessage]);
    
    try {
      // Simulate a Facebook Webhook POST to our Backend
      // This tests the RAG pipeline and Gemini integration locally
      const response = await axios.post('http://localhost:8000/api/v1/webhooks/facebook', {
        object: "page",
        entry: [{
          messaging: [{
            sender: { id: 'test-user-123' },
            message: { text: input }
          }]
        }]
      });
      
      setMessages(prev => [...prev, { text: "System: Webhook sent successfully. Check backend logs for AI response.", isBot: true }]);
    } catch (error) {
      console.error('Error simulating webhook:', error);
      setMessages(prev => [...prev, { text: "System Error: Could not reach backend.", isBot: true }]);
    }
    setInput('');
  };

  return (
    <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto', fontFamily: 'Arial' }}>
      <h1>AI Chatbot Admin & Test Dashboard</h1>
      <p>Use this to test your RAG & Gemini logic before connecting to Facebook Messenger.</p>
      
      <div style={{ 
        border: '1px solid #ddd', 
        height: '400px', 
        overflowY: 'scroll', 
        padding: '15px',
        backgroundColor: '#f9f9f9',
        borderRadius: '8px',
        marginBottom: '10px'
      }}>
        {messages.map((m, i) => (
          <div key={i} style={{ marginBottom: '10px', textAlign: m.isBot ? 'left' : 'right' }}>
            <span style={{ 
              display: 'inline-block', 
              padding: '8px 12px', 
              borderRadius: '15px', 
              backgroundColor: m.isBot ? '#e1e1e1' : '#0084ff',
              color: m.isBot ? '#000' : '#fff'
            }}>
              {m.text}
            </span>
          </div>
        ))}
      </div>
      
      <div style={{ display: 'flex', gap: '10px' }}>
        <input 
          style={{ flex: 1, padding: '10px', borderRadius: '4px', border: '1px solid #ccc' }}
          value={input} 
          onChange={(e) => setInput(e.target.value)} 
          onKeyPress={(e) => e.key === 'Enter' && simulateFacebookMessage()}
          placeholder="Type 'What is Treelight?' or 'Learn: something new'..." 
        />
        <button 
          style={{ padding: '10px 20px', borderRadius: '4px', border: 'none', backgroundColor: '#0084ff', color: '#fff', cursor: 'pointer' }}
          onClick={simulateFacebookMessage}
        >
          Test Webhook
        </button>
      </div>

      <div style={{ marginTop: '20px', padding: '15px', border: '1px solid #ffcc00', backgroundColor: '#fff9e6', borderRadius: '8px' }}>
        <h3>?? Facebook Messenger Setup Checklist</h3>
        <ol>
          <li>Run <code>ngrok http 8000</code></li>
          <li>Copy the HTTPS URL to Facebook Developer Console.</li>
          <li>Set Webhook URL to: <code>YOUR_NGROK_URL/api/v1/webhooks/facebook</code></li>
          <li>Use Verify Token: <code>{import.meta.env.VITE_FB_VERIFY_TOKEN || "MY_SECURE_rANDOM_TOKEN"}</code></li>
        </ol>
      </div>
    </div>
  );
}

export default App;
