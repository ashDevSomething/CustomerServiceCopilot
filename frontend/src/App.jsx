import React, { useState, useRef, useEffect } from 'react';
import { Send, Upload, User, Bot, AlertTriangle, MessageSquare, BarChart2, Shield } from 'lucide-react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am your AI Support Copilot. How can I assist you today?', sentiment: 'Neutral' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [escalated, setEscalated] = useState(false);
  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post(`${API_BASE}/chat`, {
        message: input,
        history: messages.slice(-5) // Send last 5 messages for context
      });

      const aiMessage = {
        role: 'assistant',
        content: response.data.answer,
        sentiment: response.data.sentiment,
        escalate: response.data.escalate
      };

      if (aiMessage.escalate) {
        setEscalated(true);
      }

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error. Please make sure the backend is running and the API key is configured.', 
        sentiment: 'Neutral' 
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      await axios.post(`${API_BASE}/ingest`, formData);
      alert('Document ingested successfully!');
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Failed to ingest document.');
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar glass">
        <div className="logo">SUPPORT COPILOT</div>
        
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#818cf8' }}>
            <MessageSquare size={20} />
            <span>Active Chats</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#9ca3af' }}>
            <BarChart2 size={20} />
            <span>Analytics</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#9ca3af' }}>
            <Shield size={20} />
            <span>Security</span>
          </div>
        </nav>

        <div className="upload-card glass">
          <Upload className="upload-icon" size={32} style={{ margin: '0 auto 12px' }} />
          <h3>Train Me</h3>
          <p style={{ fontSize: '0.8rem', color: '#9ca3af', margin: '8px 0 16px' }}>
            Upload FAQs, Policies or Logs to improve my context.
          </p>
          <label className="send-btn" style={{ cursor: 'pointer' }}>
            <Upload size={16} style={{ marginRight: '8px' }} />
            Upload File
            <input type="file" hidden onChange={handleFileUpload} />
          </label>
        </div>
      </aside>

      {/* Main Chat Section */}
      <main className="chat-section">
        <header className="chat-header glass">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ width: '10px', height: '10px', background: '#22c55e', borderRadius: '50%', boxShadow: '0 0 10px #22c55e' }}></div>
            <h2 style={{ fontSize: '1.1rem' }}>AI Agent System</h2>
          </div>
          <div style={{ display: 'flex', gap: '12px' }}>
            {escalated && <span className="badge badge-escalate">Escalation Triggered</span>}
            <span className="badge badge-positive">System Active</span>
          </div>
        </header>

        <div className="chat-messages glass">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role === 'user' ? 'user-message' : 'ai-message'}`}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px', opacity: 0.7 }}>
                {msg.role === 'user' ? <User size={14} /> : <Bot size={14} />}
                <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>
                  {msg.role === 'user' ? 'YOU' : 'AI COPILOT'}
                </span>
                {msg.sentiment && (
                  <span className={`badge badge-${msg.sentiment.toLowerCase()}`} style={{ fontSize: '0.6rem', padding: '2px 6px' }}>
                    {msg.sentiment}
                  </span>
                )}
              </div>
              <div>{msg.content}</div>
            </div>
          ))}
          {loading && (
            <div className="message ai-message" style={{ display: 'flex', gap: '4px' }}>
              <span style={{ animation: 'pulse 1s infinite' }}>.</span>
              <span style={{ animation: 'pulse 1s infinite 0.2s' }}>.</span>
              <span style={{ animation: 'pulse 1s infinite 0.4s' }}>.</span>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        <div className="chat-input-container">
          <div className="input-wrapper glass">
            <input 
              type="text" 
              placeholder="Type your question here..." 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            />
            <button className="send-btn" onClick={handleSend} disabled={loading}>
              <Send size={18} />
            </button>
          </div>
        </div>
      </main>

      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes pulse {
          0% { opacity: 0.3; }
          50% { opacity: 1; }
          100% { opacity: 0.3; }
        }
      `}} />
    </div>
  );
}

export default App;
