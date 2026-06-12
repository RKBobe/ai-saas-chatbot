import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE = 'http://localhost:8000/api/v1';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [clientId, setClientId] = useState('default');
  
  // Data States
  const [inventory, setInventory] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [logs, setLogs] = useState([]);
  
  // Form States
  const [newInv, setNewInv] = useState({ sku: '', name: '', description: '', price: 0, stock_quantity: 0 });
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedCsv, setSelectedCsv] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [invSearch, setInvSearch] = useState('');
  
  // Scheduler States
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [newApt, setNewApt] = useState({ name: '', phone: '', time: '09:00 AM' });
  
  // Simulator States
  // Web Widget
  const [webChat, setWebChat] = useState([]);
  const [webInput, setWebInput] = useState('');
  const [webUserId, setWebUserId] = useState('web-user-' + Math.random().toString(36).substr(2, 5));
  
  // SMS Simulator
  const [smsChat, setSmsChat] = useState([]);
  const [smsInput, setSmsInput] = useState('');
  const [smsPhone, setSmsPhone] = useState('+15550199');
  
  // Voice Simulator
  const [voiceChat, setVoiceChat] = useState([]);
  const [voiceInput, setVoiceInput] = useState('');
  const [voicePhone, setVoicePhone] = useState('+15550244');
  const [callActive, setCallActive] = useState(false);

  // References for scroll
  const webEndRef = useRef(null);
  const smsEndRef = useRef(null);
  const voiceEndRef = useRef(null);

  // Load backend data
  const fetchData = async () => {
    try {
      // 1. Fetch inventory
      const invRes = await axios.get(`${API_BASE}/inventory/?client_id=${clientId}&query=${invSearch}`);
      setInventory(invRes.data);
      
      // 2. Fetch appointments
      const aptRes = await axios.get(`${API_BASE}/appointments/?client_id=${clientId}&date=${selectedDate}`);
      setAppointments(aptRes.data);
      
      // 3. Fetch documents
      const docRes = await axios.get(`${API_BASE}/documents/`);
      setDocuments(docRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
      addLog('Failed to synchronize dashboard with backend services.', 'warning');
    }
  };

  useEffect(() => {
    fetchData();
  }, [clientId, selectedDate, invSearch]);

  useEffect(() => {
    webEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [webChat]);
  
  useEffect(() => {
    smsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [smsChat]);

  useEffect(() => {
    voiceEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [voiceChat]);

  const addLog = (message, type = 'info') => {
    const time = new Date().toLocaleTimeString();
    setLogs(prev => [{ time, message, type }, ...prev].slice(0, 50));
  };

  // Document Management
  const handleFileUpload = async () => {
    if (!selectedFile) return;
    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    try {
      const res = await axios.post(`${API_BASE}/documents/upload?client_id=${clientId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      addLog(res.data.message, 'success');
      setSelectedFile(null);
      // Reset input element
      document.getElementById('doc-upload-input').value = '';
      fetchData();
    } catch (error) {
      addLog('Error uploading document: ' + (error.response?.data?.detail || error.message), 'danger');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteDoc = async (filename) => {
    try {
      await axios.delete(`${API_BASE}/documents/${filename}`);
      addLog(`Document '${filename}' deleted.`, 'info');
      fetchData();
    } catch (error) {
      addLog('Failed to delete document: ' + error.message, 'danger');
    }
  };

  // Inventory Management
  const handleCreateOrUpdateInventory = async (e) => {
    e.preventDefault();
    if (!newInv.sku || !newInv.name) return;
    try {
      const res = await axios.post(`${API_BASE}/inventory/?client_id=${clientId}`, newInv);
      addLog(`Inventory SKU '${res.data.sku}' saved successfully.`, 'success');
      setNewInv({ sku: '', name: '', description: '', price: 0, stock_quantity: 0 });
      fetchData();
    } catch (error) {
      addLog('Failed to save inventory item: ' + error.message, 'danger');
    }
  };

  const handleDeleteInventory = async (id) => {
    try {
      await axios.delete(`${API_BASE}/inventory/${id}?client_id=${clientId}`);
      addLog(`Inventory item removed.`, 'info');
      fetchData();
    } catch (error) {
      addLog('Failed to delete inventory item: ' + error.message, 'danger');
    }
  };

  const handleCsvUpload = async () => {
    if (!selectedCsv) return;
    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', selectedCsv);
    try {
      const res = await axios.post(`${API_BASE}/inventory/upload-csv?client_id=${clientId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      addLog(res.data.message, 'success');
      setSelectedCsv(null);
      document.getElementById('csv-upload-input').value = '';
      fetchData();
    } catch (error) {
      addLog('Failed to process CSV file: ' + (error.response?.data?.detail || error.message), 'danger');
    } finally {
      setIsUploading(false);
    }
  };

  // Appointment Booking
  const handleBookAppointment = async (e) => {
    e.preventDefault();
    if (!newApt.name || !newApt.phone) return;
    
    // Convert date + time to ISOString
    // time format is e.g. "09:00 AM" or "02:00 PM"
    try {
      const timeParts = newApt.time.split(' ');
      const clockParts = timeParts[0].split(':');
      let hour = parseInt(clockParts[0]);
      const minute = parseInt(clockParts[1]);
      if (timeParts[1] === 'PM' && hour < 12) hour += 12;
      if (timeParts[1] === 'AM' && hour === 12) hour = 0;
      
      const startDateTime = new Date(selectedDate);
      startDateTime.setHours(hour, minute, 0, 0);
      
      await axios.post(`${API_BASE}/appointments/?client_id=${clientId}`, {
        customer_name: newApt.name,
        customer_phone: newApt.phone,
        start_time: startDateTime.toISOString(),
        notes: 'Manually booked via Admin console',
        status: 'scheduled'
      });
      
      addLog(`Appointment created for ${newApt.name}.`, 'success');
      setNewApt({ name: '', phone: '', time: '09:00 AM' });
      fetchData();
    } catch (error) {
      addLog('Failed to book appointment: ' + (error.response?.data?.detail || error.message), 'danger');
    }
  };

  const handleCancelAppointment = async (id) => {
    try {
      await axios.delete(`${API_BASE}/appointments/${id}?client_id=${clientId}`);
      addLog(`Appointment cancelled.`, 'info');
      fetchData();
    } catch (error) {
      addLog('Failed to cancel appointment: ' + error.message, 'danger');
    }
  };

  // Simulators communication
  // 1. Web Widget
  const sendWebMessage = async () => {
    if (!webInput.trim()) return;
    const msgText = webInput.trim();
    setWebChat(prev => [...prev, { text: msgText, isBot: false }]);
    setWebInput('');
    addLog(`[Web Simulator] User: "${msgText}"`, 'info');
    
    try {
      const res = await axios.post(`${API_BASE}/chat/`, {
        message: msgText,
        client_id: clientId,
        user_id: webUserId
      });
      setWebChat(prev => [...prev, { text: res.data.reply, isBot: true }]);
      addLog(`[Web Simulator] Agent: "${res.data.reply}"`, 'success');
    } catch (error) {
      setWebChat(prev => [...prev, { text: 'Connection error. Check backend console.', isBot: true }]);
      addLog('Web Simulator POST call failed.', 'danger');
    }
  };

  // 2. SMS Simulator (sends FormData to Twilio webhook endpoint)
  const sendSmsMessage = async () => {
    if (!smsInput.trim()) return;
    const msgText = smsInput.trim();
    setSmsChat(prev => [...prev, { text: msgText, isBot: false }]);
    setSmsInput('');
    addLog(`[SMS Webhook Trigger] From ${smsPhone}: "${msgText}"`, 'info');
    
    try {
      const params = new URLSearchParams();
      params.append('Body', msgText);
      params.append('From', smsPhone);
      
      const res = await axios.post(`${API_BASE}/sms/twilio?client_id=${clientId}`, params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      
      // Parse XML TwiML Response
      const xmlText = res.data;
      const parser = new DOMParser();
      const xmlDoc = parser.parseFromString(xmlText, 'text/xml');
      const messages = xmlDoc.getElementsByTagName('Message');
      
      let botReply = '';
      if (messages.length > 0) {
        botReply = messages[0].textContent;
      } else {
        botReply = '[Empty Response]';
      }
      
      setSmsChat(prev => [...prev, { text: botReply, isBot: true, rawXml: xmlText }]);
      addLog(`[SMS Webhook Response] TwiML XML received. Message: "${botReply}"`, 'success');
    } catch (error) {
      setSmsChat(prev => [...prev, { text: 'Twilio SMS Webhook error.', isBot: true }]);
      addLog('SMS Webhook POST call failed.', 'danger');
    }
  };

  // Helper to speak text out loud using standard browser Web Speech API
  const speakText = (text) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel(); // Cancel any ongoing speech
      if (text) {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        window.speechSynthesis.speak(utterance);
      }
    }
  };

  // 3. Voice Simulator (sends speech transcripts and processes conversational IVR turns)
  const startVoiceCall = async () => {
    setCallActive(true);
    setVoiceChat([{ text: '📞 Call started. Connection established.', isSystem: true }]);
    addLog(`[Voice Call Webhook] Ringing starting...`, 'info');
    
    try {
      const params = new URLSearchParams();
      params.append('From', voicePhone);
      
      const res = await axios.post(`${API_BASE}/voice/twilio?client_id=${clientId}`, params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      
      const xmlText = res.data;
      const parsed = parseTwiML(xmlText);
      setVoiceChat(prev => [...prev, { text: parsed.spoken, isBot: true, rawXml: xmlText }]);
      addLog(`[Voice Call Webhook] Call Answered. Agent spoke greeting.`, 'success');
      
      // Speak the greeting
      speakText(parsed.spoken);
    } catch (error) {
      setVoiceChat(prev => [...prev, { text: 'Failed to initiate Twilio Call.', isSystem: true }]);
    }
  };

  const endVoiceCall = () => {
    setCallActive(false);
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setVoiceChat(prev => [...prev, { text: '📞 Call ended by user.', isSystem: true }]);
    addLog('[Voice Call] Call hung up.', 'info');
  };

  const sendVoiceSpeech = async () => {
    if (!voiceInput.trim() || !callActive) return;
    const speechText = voiceInput.trim();
    setVoiceChat(prev => [...prev, { text: `User said: "${speechText}"`, isBot: false }]);
    setVoiceInput('');
    addLog(`[Voice Call STT Turn] SpeechResult: "${speechText}"`, 'info');
    
    try {
      const params = new URLSearchParams();
      params.append('From', voicePhone);
      params.append('SpeechResult', speechText);
      
      const res = await axios.post(`${API_BASE}/voice/twilio/process?client_id=${clientId}`, params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      
      const xmlText = res.data;
      const parsed = parseTwiML(xmlText);
      setVoiceChat(prev => [...prev, { text: parsed.spoken, isBot: true, rawXml: xmlText }]);
      addLog(`[Voice Call TTS Reply] Spoken: "${parsed.spoken}"`, 'success');
      
      // Speak the bot's response
      speakText(parsed.spoken);
      
      if (!parsed.hasGather) {
        setCallActive(false);
        setVoiceChat(prev => [...prev, { text: '📞 Call disconnected by system.', isSystem: true }]);
        addLog('[Voice Call] Agent ended session.', 'info');
      }
    } catch (error) {
      setVoiceChat(prev => [...prev, { text: 'Error processing speech hook.', isSystem: true }]);
    }
  };

  const parseTwiML = (xmlText) => {
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(xmlText, 'text/xml');
    const gathers = xmlDoc.getElementsByTagName('Gather');
    const hasGather = gathers.length > 0;
    
    let spokenText = '';
    let gatherPrompt = '';
    
    if (hasGather) {
      // If there's a Gather, we only speak the Say tags INSIDE the Gather
      const gatherSays = gathers[0].getElementsByTagName('Say');
      for (let i = 0; i < gatherSays.length; i++) {
        spokenText += gatherSays[i].textContent + ' ';
      }
      gatherPrompt = spokenText.trim();
    } else {
      // If there is no Gather, we speak all Say tags (e.g. system messages or final goodbye)
      const says = xmlDoc.getElementsByTagName('Say');
      for (let i = 0; i < says.length; i++) {
        spokenText += says[i].textContent + ' ';
      }
    }
    
    return {
      spoken: spokenText.trim(),
      gather: gatherPrompt.trim(),
      hasGather
    };
  };

  // Helper calendar time slots list
  const getTimeslots = () => {
    const times = [];
    for (let hour = 9; hour < 17; hour++) {
      const hr12 = hour <= 12 ? hour : hour - 12;
      const ampm = hour < 12 ? 'AM' : 'PM';
      times.push(`${hr12 < 10 ? '0' + hr12 : hr12}:00 ${ampm}`);
    }
    return times;
  };

  return (
    <div className="admin-dashboard">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="brand">
          <div className="brand-icon">💼</div>
          <div className="brand-name">CoreTex Office</div>
        </div>
        
        <div className="nav-menu">
          <div className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('dashboard')}>
            <span className="nav-icon">📊</span> Analytics & Logs
          </div>
          <div className={`nav-item ${activeTab === 'knowledge' ? 'active' : ''}`} onClick={() => setActiveTab('knowledge')}>
            <span className="nav-icon">📄</span> Config & Knowledge
          </div>
          <div className={`nav-item ${activeTab === 'inventory' ? 'active' : ''}`} onClick={() => setActiveTab('inventory')}>
            <span className="nav-icon">📦</span> Inventory Manager
          </div>
          <div className={`nav-item ${activeTab === 'calendar' ? 'active' : ''}`} onClick={() => setActiveTab('calendar')}>
            <span className="nav-icon">📅</span> Calendar Booking
          </div>
          <div className={`nav-item ${activeTab === 'simulator' ? 'active' : ''}`} onClick={() => setActiveTab('simulator')}>
            <span className="nav-icon">🧪</span> Testing Simulators
          </div>
        </div>

        <div className="form-group" style={{ marginTop: '20px' }}>
          <label className="form-label" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>ORGANIZATION ID</label>
          <input 
            className="form-input" 
            style={{ padding: '8px 12px', fontSize: '12px' }}
            value={clientId} 
            onChange={(e) => setClientId(e.target.value)} 
          />
        </div>

        <div className="sidebar-footer">
          <p>Office Admin v1.0.0</p>
          <p>Powered by Gemini 3.1 Pro</p>
        </div>
      </div>

      {/* Main Workspace */}
      <div className="main-content">
        <div className="content-header">
          <div className="header-title">
            <h2>{activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} Control</h2>
            <p>Managing org: <span style={{ color: 'var(--accent-purple)', fontWeight: '600' }}>{clientId}</span></p>
          </div>
          <div className="system-status">
            <div className="status-dot"></div>
            <span>Agent Active</span>
          </div>
        </div>

        {/* --- TAB 1: DASHBOARD --- */}
        {activeTab === 'dashboard' && (
          <div>
            <div className="metrics-grid">
              <div className="metric-card">
                <div className="metric-header">
                  <span className="metric-label">ACTIVE APPOINTMENTS</span>
                  <span className="metric-icon" style={{ color: 'var(--accent-purple)' }}>📅</span>
                </div>
                <div className="metric-val">{appointments.filter(a => a.status !== 'cancelled').length}</div>
                <div className="metric-desc">Scheduled for {selectedDate}</div>
              </div>
              <div className="metric-card">
                <div className="metric-header">
                  <span className="metric-label">INVENTORY SKUS</span>
                  <span className="metric-icon" style={{ color: 'var(--accent-blue)' }}>📦</span>
                </div>
                <div className="metric-val">{inventory.length}</div>
                <div className="metric-desc">Baseline seeded from docs</div>
              </div>
              <div className="metric-card">
                <div className="metric-header">
                  <span className="metric-label">KNOWLEDGE BASE DOCS</span>
                  <span className="metric-icon" style={{ color: 'var(--accent-emerald)' }}>📄</span>
                </div>
                <div className="metric-val">{documents.length}</div>
                <div className="metric-desc">PDF/MD/TXT active rules</div>
              </div>
              <div className="metric-card">
                <div className="metric-header">
                  <span className="metric-label">INTEGRATED CHANNELS</span>
                  <span className="metric-icon" style={{ color: 'var(--accent-amber)' }}>🔌</span>
                </div>
                <div className="metric-val">3</div>
                <div className="metric-desc">Web Chat, SMS, Voice Calls</div>
              </div>
            </div>

            <div className="dashboard-card">
              <div className="dashboard-card-title">💬 Live System Logs & Webhook Traffic</div>
              <div className="table-container" style={{ maxHeight: '350px', overflowY: 'auto' }}>
                <div className="log-list">
                  {logs.length === 0 ? (
                    <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)' }}>No logs captured yet. Send a message in the simulators to see webhook activity!</div>
                  ) : (
                    logs.map((log, index) => (
                      <div key={index} className={`log-item ${log.type}`}>
                        <div className="log-meta">
                          <span style={{ fontWeight: '600' }}>{log.time}</span>
                          <span className={`badge ${log.type === 'success' ? 'badge-success' : log.type === 'warning' ? 'badge-warning' : log.type === 'danger' ? 'badge-danger' : 'badge-info'}`}>
                            {log.type.toUpperCase()}
                          </span>
                        </div>
                        <div>{log.message}</div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* --- TAB 2: KNOWLEDGE BASE --- */}
        {activeTab === 'knowledge' && (
          <div>
            <div className="dashboard-card">
              <div className="dashboard-card-title">📁 Upload Knowledge Base Documents</div>
              <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginBottom: '20px' }}>
                Instantly make your AI assistant an expert by dropping in your company policy sheets, manuals, or PDF documents.
              </p>
              
              <div className="upload-dropzone" onClick={() => document.getElementById('doc-upload-input').click()}>
                <div className="upload-icon">📥</div>
                <h3>Click to select PDF, TXT or MD File</h3>
                <p style={{ color: 'var(--text-muted)', marginTop: '8px' }}>
                  {selectedFile ? `Selected: ${selectedFile.name}` : 'Supports: .pdf, .txt, .md'}
                </p>
              </div>
              <input 
                id="doc-upload-input"
                type="file" 
                style={{ display: 'none' }} 
                accept=".pdf,.txt,.md"
                onChange={(e) => setSelectedFile(e.target.files[0])} 
              />
              {selectedFile && (
                <div style={{ marginTop: '16px', display: 'flex', gap: '10px' }}>
                  <button className="btn btn-primary" onClick={handleFileUpload} disabled={isUploading}>
                    {isUploading ? 'Ingesting vectors...' : 'Process & Vectorize Document'}
                  </button>
                  <button className="btn btn-secondary" onClick={() => setSelectedFile(null)}>Cancel</button>
                </div>
              )}
            </div>

            <div className="dashboard-card">
              <div className="dashboard-card-title">📄 Ingested Documents ({documents.length})</div>
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Document Filename</th>
                      <th>Type</th>
                      <th>Status</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {documents.length === 0 ? (
                      <tr>
                        <td colSpan="4" style={{ textAlign: 'center', padding: '20px', color: 'var(--text-muted)' }}>
                          No documents ingested yet. Upload one above to begin.
                        </td>
                      </tr>
                    ) : (
                      documents.map((doc, idx) => (
                        <tr key={idx}>
                          <td style={{ fontWeight: '500' }}>{doc}</td>
                          <td>{doc.split('.').pop().toUpperCase()}</td>
                          <td><span className="badge badge-success">Vectorized</span></td>
                          <td>
                            <button className="btn btn-danger btn-sm" onClick={() => handleDeleteDoc(doc)}>Delete</button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* --- TAB 3: INVENTORY MANAGER --- */}
        {activeTab === 'inventory' && (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 300fr', gap: '30px', alignItems: 'start' }} className="simulators-container">
              {/* Add Inventory Form */}
              <div className="dashboard-card" style={{ height: 'fit-content' }}>
                <div className="dashboard-card-title">➕ Add/Edit Item SKU</div>
                <form onSubmit={handleCreateOrUpdateInventory}>
                  <div className="form-group">
                    <label className="form-label">SKU ID *</label>
                    <input 
                      className="form-input" 
                      required 
                      value={newInv.sku}
                      onChange={(e) => setNewInv(prev => ({ ...prev, sku: e.target.value }))}
                      placeholder="e.g. SKU-101" 
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Item Name *</label>
                    <input 
                      className="form-input" 
                      required 
                      value={newInv.name}
                      onChange={(e) => setNewInv(prev => ({ ...prev, name: e.target.value }))}
                      placeholder="e.g. Blue Widget" 
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Price ($)</label>
                    <input 
                      className="form-input" 
                      type="number" 
                      step="0.01" 
                      value={newInv.price}
                      onChange={(e) => setNewInv(prev => ({ ...prev, price: parseFloat(e.target.value) || 0 }))}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Stock Quantity</label>
                    <input 
                      className="form-input" 
                      type="number" 
                      value={newInv.stock_quantity}
                      onChange={(e) => setNewInv(prev => ({ ...prev, stock_quantity: parseInt(e.target.value) || 0 }))}
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Description</label>
                    <textarea 
                      className="form-textarea" 
                      rows="3" 
                      value={newInv.description}
                      onChange={(e) => setNewInv(prev => ({ ...prev, description: e.target.value }))}
                      placeholder="Product details..."
                    />
                  </div>
                  <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>Save SKU Record</button>
                </form>
              </div>

              {/* Seed CSV and Datatable */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
                <div className="dashboard-card">
                  <div className="dashboard-card-title">📊 Seed/Sync Inventory via CSV</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                    <input 
                      id="csv-upload-input"
                      type="file" 
                      accept=".csv"
                      className="form-input"
                      style={{ padding: '8px' }}
                      onChange={(e) => setSelectedCsv(e.target.files[0])} 
                    />
                    <button className="btn btn-primary" onClick={handleCsvUpload} disabled={!selectedCsv || isUploading}>
                      {isUploading ? 'Seeding...' : 'Seed Inventory'}
                    </button>
                  </div>
                </div>

                <div className="dashboard-card">
                  <div className="dashboard-card-title">📦 Active SKU Inventory</div>
                  <div className="form-group">
                    <input 
                      className="form-input" 
                      placeholder="Search SKU ID or product name..." 
                      value={invSearch}
                      onChange={(e) => setInvSearch(e.target.value)}
                    />
                  </div>
                  <div className="table-container">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>SKU ID</th>
                          <th>Product Name</th>
                          <th>Price</th>
                          <th>Stock Level</th>
                          <th>Description</th>
                          <th>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {inventory.length === 0 ? (
                          <tr>
                            <td colSpan="6" style={{ textAlign: 'center', padding: '20px', color: 'var(--text-muted)' }}>
                              No SKUs in database. Seed from CSV or add one on the left.
                            </td>
                          </tr>
                        ) : (
                          inventory.map((item) => (
                            <tr key={item.id}>
                              <td style={{ fontFamily: 'monospace', fontWeight: '600' }}>{item.sku}</td>
                              <td style={{ fontWeight: '500' }}>{item.name}</td>
                              <td>${item.price.toFixed(2)}</td>
                              <td>
                                <span className={`badge ${item.stock_quantity > 0 ? 'badge-success' : 'badge-danger'}`}>
                                  {item.stock_quantity} units
                                </span>
                              </td>
                              <td style={{ color: 'var(--text-muted)', fontSize: '13px' }}>{item.description || 'N/A'}</td>
                              <td>
                                <button className="btn btn-danger btn-sm" onClick={() => handleDeleteInventory(item.id)}>Delete</button>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* --- TAB 4: CALENDAR --- */}
        {activeTab === 'calendar' && (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '30px', alignItems: 'start' }} className="simulators-container">
              {/* Form to Book manually */}
              <div className="dashboard-card">
                <div className="dashboard-card-title">📅 Quick Scheduler</div>
                <div className="form-group">
                  <label className="form-label">Target Booking Date</label>
                  <input 
                    className="form-input" 
                    type="date" 
                    value={selectedDate}
                    onChange={(e) => setSelectedDate(e.target.value)}
                  />
                </div>
                <form onSubmit={handleBookAppointment}>
                  <div className="form-group">
                    <label className="form-label">Customer Name *</label>
                    <input 
                      className="form-input" 
                      required 
                      value={newApt.name}
                      onChange={(e) => setNewApt(prev => ({ ...prev, name: e.target.value }))}
                      placeholder="John Doe" 
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Phone Number *</label>
                    <input 
                      className="form-input" 
                      required 
                      value={newApt.phone}
                      onChange={(e) => setNewApt(prev => ({ ...prev, phone: e.target.value }))}
                      placeholder="+1 (555) 0123" 
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Time Slot</label>
                    <select 
                      className="form-select"
                      value={newApt.time}
                      onChange={(e) => setNewApt(prev => ({ ...prev, time: e.target.value }))}
                    >
                      {getTimeslots().map((slot, index) => (
                        <option key={index} value={slot}>{slot}</option>
                      ))}
                    </select>
                  </div>
                  <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>Book Slot</button>
                </form>
              </div>

              {/* Agenda Slot view */}
              <div className="dashboard-card">
                <div className="dashboard-card-title">📋 Agenda Schedule for {selectedDate}</div>
                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Time Slot</th>
                        <th>Status</th>
                        <th>Booked Client Name</th>
                        <th>Contact Phone</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {getTimeslots().map((slot, idx) => {
                        // Check if an appointment fits this hour
                        // slot format is "09:00 AM" -> check hour
                        const timeParts = slot.split(' ');
                        const clockParts = timeParts[0].split(':');
                        let slotHour = parseInt(clockParts[0]);
                        if (timeParts[1] === 'PM' && slotHour < 12) slotHour += 12;
                        if (timeParts[1] === 'AM' && slotHour === 12) slotHour = 0;
                        
                        const booking = appointments.find(a => {
                          const dt = new Date(a.start_time);
                          return dt.getHours() === slotHour && a.status !== 'cancelled';
                        });
                        
                        return (
                          <tr key={idx} style={booking ? { backgroundColor: 'rgba(99, 102, 241, 0.02)' } : {}}>
                            <td style={{ fontWeight: '600' }}>{slot}</td>
                            <td>
                              {booking ? (
                                <span className="badge badge-warning">Booked</span>
                              ) : (
                                <span className="badge badge-success">Available</span>
                              )}
                            </td>
                            <td>{booking ? booking.customer_name : '-'}</td>
                            <td style={{ fontFamily: 'monospace' }}>{booking ? booking.customer_phone : '-'}</td>
                            <td>
                              {booking ? (
                                <button className="btn btn-danger btn-sm" onClick={() => handleCancelAppointment(booking.id)}>Cancel</button>
                              ) : (
                                <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>Open to Scheduling</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* --- TAB 5: TESTING SIMULATORS --- */}
        {activeTab === 'simulator' && (
          <div>
            <div className="simulators-container">
              {/* Web Simulator */}
              <div className="sim-panel">
                <div className="sim-header">
                  <div className="sim-title">🌐 Web Widget Simulator</div>
                  <span className="sim-badge">ID: {webUserId}</span>
                </div>
                <div className="sim-body">
                  {webChat.length === 0 && (
                    <div className="bubble-system">Ask for inventory, schedules, or FAQs to test local knowledge vectors.</div>
                  )}
                  {webChat.map((msg, i) => (
                    <div key={i} className={`bubble ${msg.isBot ? 'bubble-bot' : 'bubble-user'}`}>
                      {msg.text}
                    </div>
                  ))}
                  <div ref={webEndRef} />
                </div>
                <div className="sim-footer">
                  <input 
                    className="sim-input" 
                    placeholder="Type a web message..." 
                    value={webInput}
                    onChange={(e) => setWebInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendWebMessage()}
                  />
                  <button className="btn btn-primary btn-sm" onClick={sendWebMessage}>Send</button>
                </div>
              </div>

              {/* SMS Simulator */}
              <div className="sim-panel">
                <div className="sim-header">
                  <div className="sim-title">📱 Twilio SMS Simulator</div>
                  <input 
                    className="sim-input" 
                    style={{ maxWidth: '120px', padding: '4px 8px', fontSize: '11px' }}
                    value={smsPhone}
                    onChange={(e) => setSmsPhone(e.target.value)}
                    placeholder="From Phone"
                  />
                </div>
                <div className="sim-body">
                  {smsChat.length === 0 && (
                    <div className="bubble-system">Simulate incoming Twilio SMS API webhook signals. Responses are parsed TwiML.</div>
                  )}
                  {smsChat.map((msg, i) => (
                    <React.Fragment key={i}>
                      <div className={`bubble ${msg.isBot ? 'bubble-bot' : 'bubble-user'}`}>
                        {msg.text}
                        {msg.rawXml && (
                          <div className="bubble-code">
                            <strong>XML Response Received:</strong>
                            {msg.rawXml}
                          </div>
                        )}
                      </div>
                    </React.Fragment>
                  ))}
                  <div ref={smsEndRef} />
                </div>
                <div className="sim-footer">
                  <input 
                    className="sim-input" 
                    placeholder="Type SMS text..." 
                    value={smsInput}
                    onChange={(e) => setSmsInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendSmsMessage()}
                  />
                  <button className="btn btn-primary btn-sm" onClick={sendSmsMessage}>Send</button>
                </div>
              </div>

              {/* Voice Simulator */}
              <div className="sim-panel">
                <div className="sim-header">
                  <div className="sim-title">📞 Twilio Voice (IVR) Simulator</div>
                  <input 
                    className="sim-input" 
                    style={{ maxWidth: '120px', padding: '4px 8px', fontSize: '11px' }}
                    value={voicePhone}
                    onChange={(e) => setVoicePhone(e.target.value)}
                    placeholder="From Phone"
                    disabled={callActive}
                  />
                </div>
                <div className="sim-body">
                  {voiceChat.map((msg, i) => (
                    <div key={i} className={msg.isSystem ? 'bubble-system' : `bubble ${msg.isBot ? 'bubble-bot' : 'bubble-user'}`}>
                      {msg.isSystem ? (
                        msg.text
                      ) : (
                        <>
                          {msg.isBot ? '🤖 TTS: ' : '🗣️ Speaking: '}"{msg.text}"
                          {msg.rawXml && (
                            <div className="bubble-code">
                              <strong>TwiML Output XML:</strong>
                              {msg.rawXml}
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  ))}
                  <div ref={voiceEndRef} />
                </div>
                <div className="sim-footer">
                  {!callActive ? (
                    <button className="btn btn-primary" style={{ width: '100%' }} onClick={startVoiceCall}>
                      📞 Place Call to Webhook
                    </button>
                  ) : (
                    <>
                      <input 
                        className="sim-input" 
                        placeholder="Simulate speaking/transcribing speech..." 
                        value={voiceInput}
                        onChange={(e) => setVoiceInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && sendVoiceSpeech()}
                      />
                      <button className="btn btn-primary btn-sm" onClick={sendVoiceSpeech}>Speak</button>
                      <button className="btn btn-danger btn-sm" onClick={endVoiceCall}>Hang Up</button>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
