import React, { useState, useRef, useEffect } from 'react';
import { BsChatDotsFill, BsRobot, BsLightningChargeFill, BsBrain, BsSparkles } from 'react-icons/bs';
import { FaPaperPlane, FaTimes, FaMoon, FaSun, FaHistory, FaPlus, FaEdit, FaTrash, FaRobot, FaUserCircle, FaMagic, FaWandMagicSparkles, FaComments, FaMessage } from 'react-icons/fa';
import { RiAiGenerate, RiChatSmile3Fill, RiRobot2Fill, RiMagicFill } from 'react-icons/ri';
import { GiBrain, GiCrystalBall, GiMagicPortal } from 'react-icons/gi';
import { TbRobot, TbBrain, TbSparkles } from 'react-icons/tb';
import api from '../../utils/axios';
import { useAuth } from '../../contexts/AuthContext';

const CHAT_SESSIONS_KEY = 'ai_chatbot_sessions';
const THEME_KEY = 'ai_chatbot_theme';

function generateSessionId() {
  return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6);
}

const getInitialTheme = () => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem(THEME_KEY) || 'light';
  }
  return 'light';
};

const getChatKey = (user) => user?.email ? `ai_chatbot_sessions_${user.email}` : 'ai_chatbot_sessions';

const getInitialSessions = (user) => {
  if (typeof window !== 'undefined') {
    try {
      return JSON.parse(localStorage.getItem(getChatKey(user)) || '[]');
    } catch {
      return [];
    }
  }
  return [];
};

const getSessionName = (session) => {
  if (session.name && session.name.trim() !== '') return session.name;
  const firstMsg = session.messages?.find((m) => m.sender === 'user');
  if (firstMsg && firstMsg.text) {
    return firstMsg.text.split(' ').slice(0, 7).join(' ') + (firstMsg.text.split(' ').length > 7 ? '...' : '');
  }
  return 'New Chat';
};

const TypingIndicator = ({ isDark }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 6, margin: '8px 0 8px 8px' }}>
    <div style={{ 
      width: 32, 
      height: 32, 
      borderRadius: '50%', 
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      boxShadow: '0 3px 10px rgba(102, 126, 234, 0.3)',
      border: '1px solid rgba(255,255,255,0.1)',
      position: 'relative',
      overflow: 'hidden',
    }}>
      <TbRobot color="#fff" size={18} style={{ filter: 'drop-shadow(0 0 3px rgba(255,255,255,0.3))' }} />
      {/* Animated glow */}
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        width: '100%',
        height: '100%',
        transform: 'translate(-50%, -50%)',
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%)',
        animation: 'typingPulse 2s infinite',
      }} />
    </div>
    <div className="typing-indicator">
      <span></span><span></span><span></span>
    </div>
    <style>{`
      .typing-indicator span {
        display: inline-block;
        width: 8px;
        height: 8px;
        margin: 0 3px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 50%;
        opacity: 0.8;
        animation: typing-bounce 1.2s infinite both;
        box-shadow: 0 2px 6px rgba(102, 126, 234, 0.3);
        border: 1px solid rgba(255,255,255,0.2);
      }
      .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
      .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
      @keyframes typing-bounce {
        0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
        40% { transform: scale(1.3); opacity: 1; }
      }
    `}</style>
  </div>
);

const Chatbot: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState('');
  const [sessions, setSessions] = useState<any[]>(() => getInitialSessions(user));
  const [currentSessionId, setCurrentSessionId] = useState<string>(() => {
    const sessions = getInitialSessions(user);
    return sessions.length > 0 ? sessions[sessions.length - 1].id : generateSessionId();
  });
  const [theme, setTheme] = useState<'light' | 'dark'>(getInitialTheme() as 'light' | 'dark');
  const [showHistory, setShowHistory] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const chatEndRef = useRef<HTMLDivElement>(null);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');

  // Get messages for current session
  const messages = sessions.find(s => s.id === currentSessionId)?.messages || [];

  useEffect(() => {
    if (open && chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, open]);

  useEffect(() => {
    if (user) {
      localStorage.setItem(getChatKey(user), JSON.stringify(sessions));
    }
  }, [sessions, user]);

  // Jab user change ho (login/logout), apni chat history load karo
  useEffect(() => {
    setSessions(getInitialSessions(user));
  }, [user]);

  useEffect(() => {
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  // Listen for navbar chatbot button click
  useEffect(() => {
    const handleOpenChatbot = () => {
      setOpen(true);
    };

    window.addEventListener('openChatbot', handleOpenChatbot);
    return () => {
      window.removeEventListener('openChatbot', handleOpenChatbot);
    };
  }, []);

  if (!isAuthenticated) {
    return (
      <div
        style={{
          position: 'fixed',
          top: '120px',
          right: '20px',
          width: 390,
          maxWidth: '98vw',
          height: 120,
          background: 'rgba(255,255,255,0.95)',
          borderRadius: 24,
          boxShadow: '0 8px 32px rgba(0,0,0,0.18)',
          zIndex: 99999,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: 'Inter, Segoe UI, Arial, sans-serif',
          border: '2.5px solid #e0e7ef',
          backdropFilter: 'blur(16px)',
        }}
      >
        <span style={{ fontWeight: 700, fontSize: 20, color: '#2563eb' }}>
          Please login to use AI chat
        </span>
      </div>
    );
  }

  const sendMessage = async () => {
    if (!input.trim()) return;
    const newUserMsg = { sender: 'user', text: input };
    updateSessionMessages([...messages, newUserMsg]);
    setLoading(true);
    setError('');
    try {
      const res = await api.post('/chatbot', { message: input });
      const reply = res.data.reply || 'Sorry, AI could not reply.';
      updateSessionMessages([...messages, newUserMsg, { sender: 'ai', text: reply }]);
    } catch (err: any) {
      console.error('Chatbot error:', err);
      updateSessionMessages([...messages, newUserMsg, { sender: 'ai', text: 'Error: Could not get AI response.' }]);
      setError('AI se reply nahi aaya.');
    } finally {
      setLoading(false);
      setInput('');
    }
  };

  const updateSessionMessages = (msgs: any[]) => {
    setSessions(prev => prev.map(s => s.id === currentSessionId ? { ...s, messages: msgs } : s));
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') sendMessage();
  };

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  const startNewChat = () => {
    const newId = generateSessionId();
    setSessions(prev => [...prev, { id: newId, created: Date.now(), messages: [], name: '' }]);
    setCurrentSessionId(newId);
    setError('');
    setInput('');
  };

  const openSession = (id: string) => {
    setCurrentSessionId(id);
    setShowHistory(false);
    setError('');
    setInput('');
    setEditingSessionId(null);
  };

  const handleEditClick = (session: any) => {
    setEditingSessionId(session.id);
    setEditName(getSessionName(session));
  };

  const handleEditSave = (session: any) => {
    setSessions(prev => prev.map(s => s.id === session.id ? { ...s, name: editName } : s));
    setEditingSessionId(null);
  };

  const handleEditCancel = () => {
    setEditingSessionId(null);
  };

  const handleDeleteSession = async (id: string) => {
    try {
      // Get session details before deleting
      const sessionToDelete = sessions.find(s => s.id === id);
      const messageCount = sessionToDelete?.messages?.length || 0;
      // Delete from frontend
      setSessions(prev => prev.filter(s => s.id !== id));
      // Update backend dashboard
      if (messageCount > 0) {
        await api.post('/api/dashboard/activity', {
          type: 'chat_session_deleted',
          title: `Deleted chat session`,
          description: `Deleted chat session with ${messageCount} messages`,
          metadata: {
            session_id: id,
            message_count: messageCount
          }
        });
      }
      if (currentSessionId === id && sessions.length > 1) {
        // Switch to another session if current is deleted
        const other = sessions.find(s => s.id !== id);
        if (other) setCurrentSessionId(other.id);
      } else if (sessions.length === 1) {
        // If last session deleted, start a new one
        startNewChat();
      }
    } catch (error) {
      console.error('Error deleting chat session:', error);
    }
  };

  // Theme styles
  const isDark = theme === 'dark';
  const colors = {
    bg: isDark ? 'rgba(24,24,27,0.85)' : 'rgba(255,255,255,0.85)',
    glass: isDark ? 'rgba(36,37,46,0.55)' : 'rgba(255,255,255,0.55)',
    header: isDark
      ? 'linear-gradient(90deg, #6366f1 0%, #0ea5e9 100%)'
      : 'linear-gradient(90deg, #2563eb 0%, #38bdf8 100%)',
    userBubble: isDark ? '#2563eb' : '#2563eb',
    aiBubble: isDark ? 'rgba(39,39,42,0.85)' : 'rgba(229,231,235,0.85)',
    aiText: isDark ? '#f1f5f9' : '#222',
    userText: '#fff',
    border: isDark ? '#27272a' : '#e5e7eb',
    inputBg: isDark ? 'rgba(35,39,47,0.85)' : 'rgba(248,250,252,0.85)',
    inputText: isDark ? '#f1f5f9' : '#222',
    shadow: isDark
      ? '0 8px 32px rgba(30,41,59,0.55)'
      : '0 8px 32px rgba(0,0,0,0.18)',
    historyBg: isDark ? 'rgba(35,39,47,0.95)' : 'rgba(241,245,249,0.95)',
    historyBorder: isDark ? '#27272a' : '#e5e7eb',
    historyActive: isDark ? '#6366f1' : '#bae6fd',
    glassBorder: isDark ? 'rgba(99,102,241,0.25)' : 'rgba(56,189,248,0.18)',
  };

  return (
    <>
      {/* Chat Window */}
      {open && (
        <div
          style={{
            position: 'fixed',
            top: '120px',
            right: '20px',
            width: 390,
            maxWidth: '98vw',
            height: 540,
            background: colors.bg,
            borderRadius: 24,
            boxShadow: colors.shadow,
            zIndex: 99999,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            animation: 'fadeInUp 0.3s',
            fontFamily: 'Inter, Segoe UI, Arial, sans-serif',
            border: `2.5px solid ${colors.glassBorder}`,
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)',
            transition: 'background 0.2s',
          }}
        >
          {/* Header */}
          <div style={{
            padding: '16px 24px',
            borderBottom: `2px solid ${colors.glassBorder}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: colors.header,
            color: 'white',
            borderTopLeftRadius: 24,
            borderTopRightRadius: 24,
            fontWeight: 700,
            fontSize: 20,
            letterSpacing: 0.5,
            boxShadow: '0 2px 12px rgba(56,189,248,0.10)',
            borderBottomLeftRadius: 12,
            borderBottomRightRadius: 12,
          }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ 
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 32,
                height: 32,
                borderRadius: '50%',
                background: 'rgba(255,255,255,0.1)',
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(255,255,255,0.2)',
                marginRight: 8,
              }}>
                <TbRobot size={20} style={{ 
                  filter: 'drop-shadow(0 0 8px rgba(255,255,255,0.5))',
                  color: '#fff',
                }} />
                {/* Animated glow */}
                <div style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  width: '100%',
                  height: '100%',
                  transform: 'translate(-50%, -50%)',
                  borderRadius: '50%',
                  background: 'radial-gradient(circle, rgba(255,255,255,0.2) 0%, transparent 70%)',
                  animation: 'headerPulse 2s infinite',
                }} />
              </div>
              <span style={{ 
                textShadow: '0 2px 8px #0ea5e9',
                fontWeight: 700,
                fontSize: 22,
                background: 'linear-gradient(45deg, #fff, #e0e7ff)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }}>AI Assistant</span>
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              <button
                onClick={startNewChat}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'white',
                  cursor: 'pointer',
                  fontSize: 22,
                  marginRight: 2,
                  filter: 'drop-shadow(0 0 4px #38bdf8)',
                }}
                aria-label="Start new chat"
                title="Start new chat"
              >
                <FaPlus />
              </button>
              <button
                onClick={() => setShowHistory(true)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'white',
                  cursor: 'pointer',
                  fontSize: 22,
                  marginRight: 2,
                  filter: 'drop-shadow(0 0 4px #38bdf8)',
                }}
                aria-label="Show chat history"
                title="Show chat history"
              >
                <FaHistory />
              </button>
              <button
                onClick={toggleTheme}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'white',
                  cursor: 'pointer',
                  fontSize: 22,
                  marginRight: 2,
                  filter: 'drop-shadow(0 0 4px #38bdf8)',
                }}
                aria-label="Toggle theme"
              >
                {isDark ? <FaSun /> : <FaMoon />}
              </button>
              <FaTimes style={{ cursor: 'pointer', fontSize: 26, filter: 'drop-shadow(0 0 4px #38bdf8)' }} onClick={() => setOpen(false)} />
            </div>
          </div>
          {/* Chat Body */}
          <div style={{ flex: 1, overflowY: 'auto', padding: 22, background: 'transparent', transition: 'background 0.2s' }}>
            {messages.length === 0 && (
              <div style={{ color: '#888', textAlign: 'center', marginTop: 40, fontSize: 17 }}>
                Start chatting with AI!<br />Aap kuch bhi pooch sakte hain.
              </div>
            )}
            {messages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                  marginBottom: 16,
                  alignItems: 'flex-end',
                  animation: 'bubbleIn 0.35s',
                }}
              >
                {msg.sender === 'ai' && (
                  <div style={{ marginRight: 8, marginBottom: 2 }}>
                    <div style={{ 
                      width: 36, 
                      height: 36, 
                      borderRadius: '50%', 
                      background: isDark 
                        ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' 
                        : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center', 
                      boxShadow: '0 4px 12px rgba(102, 126, 234, 0.3)',
                      border: '2px solid rgba(255,255,255,0.1)',
                      position: 'relative',
                      overflow: 'hidden',
                    }}>
                      <TbRobot color="#fff" size={20} style={{ filter: 'drop-shadow(0 0 4px rgba(255,255,255,0.3))' }} />
                      {/* Animated glow */}
                      <div style={{
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        width: '100%',
                        height: '100%',
                        transform: 'translate(-50%, -50%)',
                        borderRadius: '50%',
                        background: 'radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%)',
                        animation: 'messagePulse 3s infinite',
                      }} />
                    </div>
                  </div>
                )}
                <div
                  style={{
                    background: msg.sender === 'user' ? colors.userBubble : colors.aiBubble,
                    color: msg.sender === 'user' ? colors.userText : colors.aiText,
                    borderRadius: 18,
                    padding: '12px 18px',
                    maxWidth: '75%',
                    fontSize: 17,
                    boxShadow: msg.sender === 'user' ? '0 2px 12px rgba(37,99,235,0.10)' : '0 2px 12px rgba(56,189,248,0.08)',
                    borderBottomRightRadius: msg.sender === 'user' ? 6 : 18,
                    borderBottomLeftRadius: msg.sender === 'ai' ? 6 : 18,
                    wordBreak: 'break-word',
                    backdropFilter: 'blur(4px)',
                    WebkitBackdropFilter: 'blur(4px)',
                    border: `1.5px solid ${colors.glassBorder}`,
                    transition: 'background 0.2s, color 0.2s',
                    animation: 'bubbleIn 0.35s',
                  }}
                >
                  {msg.text}
                </div>
                {msg.sender === 'user' && (
                  <div style={{ marginLeft: 8, marginBottom: 2 }}>
                    <div style={{ width: 32, height: 32, borderRadius: '50%', background: isDark ? '#2563eb' : '#bae6fd', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 2px 8px rgba(56,189,248,0.10)', overflow: 'hidden' }}>
                      {user?.avatar ? (
                        <img 
                                                      src={`http://localhost:5050/api/auth/avatar?${Date.now()}&user=${user?.email}`} 
                          alt="User Avatar" 
                          style={{ 
                            width: '100%', 
                            height: '100%', 
                            objectFit: 'cover',
                            borderRadius: '50%'
                          }} 
                          onError={(e) => {
                            e.currentTarget.style.display = 'none';
                            e.currentTarget.nextSibling.style.display = 'flex';
                          }}
                        />
                      ) : null}
                      <FaUserCircle 
                        color={isDark ? '#fff' : '#2563eb'} 
                        size={18} 
                        style={{ 
                          display: user?.avatar ? 'none' : 'flex',
                          position: 'absolute'
                        }} 
                      />
                    </div>
                  </div>
                )}
              </div>
            ))}
            {loading && <TypingIndicator isDark={isDark} />}
            <div ref={chatEndRef} />
          </div>
          {/* Input */}
          <div style={{ padding: 16, borderTop: `2px solid ${colors.glassBorder}`, background: colors.inputBg, borderBottomLeftRadius: 24, borderBottomRightRadius: 24, transition: 'background 0.2s', boxShadow: '0 -2px 12px rgba(56,189,248,0.08)' }}>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <input
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your message..."
                style={{
                  flex: 1,
                  padding: '12px 16px',
                  borderRadius: 12,
                  border: `2px solid ${colors.glassBorder}`,
                  fontSize: 17,
                  outline: 'none',
                  background: colors.inputBg,
                  color: colors.inputText,
                  transition: 'background 0.2s, color 0.2s',
                  boxShadow: '0 1px 4px rgba(56,189,248,0.08)',
                }}
                disabled={loading}
              />
              <button
                onClick={sendMessage}
                style={{
                  marginLeft: 12,
                  background: `linear-gradient(90deg, #2563eb 0%, #38bdf8 100%)`,
                  color: 'white',
                  border: 'none',
                  borderRadius: 12,
                  padding: '12px 16px',
                  cursor: 'pointer',
                  fontSize: 20,
                  display: 'flex',
                  alignItems: 'center',
                  boxShadow: '0 2px 8px rgba(56,189,248,0.10)',
                  transition: 'background 0.2s',
                  fontWeight: 700,
                }}
                disabled={loading || !input.trim()}
                aria-label="Send"
              >
                <FaPaperPlane />
              </button>
            </div>
            {error && <div style={{ color: 'red', marginTop: 10, fontSize: 15 }}>{error}</div>}
          </div>
          {/* Chat History Modal */}
          {showHistory && (
            <>
              {/* Overlay */}
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  background: 'rgba(0,0,0,0.18)',
                  zIndex: 1002,
                }}
                onClick={() => setShowHistory(false)}
              />
              {/* Sidebar */}
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: 300,
                  height: '100%',
                  background: colors.historyBg,
                  borderRight: `2px solid ${colors.historyBorder}`,
                  boxShadow: '2px 0 16px rgba(0,0,0,0.08)',
                  zIndex: 1003,
                  padding: '18px 0 0 0',
                  display: 'flex',
                  flexDirection: 'column',
                  animation: 'slideInLeft 0.25s',
                }}
              >
                <div style={{ fontWeight: 700, fontSize: 18, padding: '0 18px 12px 18px', color: isDark ? '#fff' : '#222' }}>
                  Chat History
                  <FaTimes style={{ float: 'right', cursor: 'pointer', fontSize: 20 }} onClick={() => setShowHistory(false)} />
                </div>
                <div style={{ flex: 1, overflowY: 'auto', padding: '0 8px' }}>
                  {sessions.length === 0 && (
                    <div style={{ color: '#888', textAlign: 'center', marginTop: 40, fontSize: 15 }}>
                      No previous chats.
                    </div>
                  )}
                  {sessions.map((s) => (
                    <div
                      key={s.id}
                      style={{
                        background: s.id === currentSessionId ? colors.historyActive : 'transparent',
                        borderRadius: 10,
                        padding: '10px 12px',
                        marginBottom: 8,
                        cursor: 'pointer',
                        color: s.id === currentSessionId ? (isDark ? '#fff' : '#222') : (isDark ? '#f1f5f9' : '#222'),
                        fontWeight: s.id === currentSessionId ? 600 : 400,
                        border: s.id === currentSessionId ? `1.5px solid ${colors.userBubble}` : '1.5px solid transparent',
                        boxShadow: s.id === currentSessionId ? '0 2px 8px rgba(37,99,235,0.10)' : 'none',
                        transition: 'background 0.2s, color 0.2s',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                      }}
                    >
                      <div style={{ flex: 1 }} onClick={() => openSession(s.id)}>
                        {editingSessionId === s.id ? (
                          <>
                            <input
                              value={editName}
                              onChange={e => setEditName(e.target.value)}
                              style={{
                                width: '90%',
                                padding: '4px 8px',
                                borderRadius: 6,
                                border: `1px solid ${colors.historyBorder}`,
                                fontSize: 15,
                                marginBottom: 2,
                              }}
                              autoFocus
                            />
                            <button onClick={() => handleEditSave(s)} style={{ marginLeft: 4, fontSize: 14, cursor: 'pointer', background: 'transparent', border: 'none', color: colors.userBubble }}>Save</button>
                            <button onClick={handleEditCancel} style={{ marginLeft: 2, fontSize: 14, cursor: 'pointer', background: 'transparent', border: 'none', color: '#888' }}>Cancel</button>
                          </>
                        ) : (
                          <>
                            <div style={{ fontSize: 15, fontWeight: 600 }}>{getSessionName(s)}</div>
                            <div style={{ fontSize: 13, color: '#888', marginTop: 2 }}>
                              {new Date(s.created).toLocaleString()} • {s.messages.length} message{s.messages.length !== 1 ? 's' : ''}
                            </div>
                          </>
                        )}
                      </div>
                      {editingSessionId !== s.id && (
                        <>
                          <FaEdit style={{ cursor: 'pointer', fontSize: 16, marginRight: 6 }} onClick={() => handleEditClick(s)} title="Edit name" />
                          <FaTrash style={{ cursor: 'pointer', fontSize: 16, color: '#e11d48' }} onClick={() => handleDeleteSession(s.id)} title="Delete chat" />
                        </>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      )}
      {/* Animation keyframes */}
      <style>{`
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(40px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slideInLeft {
          from { opacity: 0; transform: translateX(-40px); }
          to { opacity: 1; transform: translateX(0); }
        }
        @keyframes bubbleIn {
          from { opacity: 0; transform: translateY(20px) scale(0.95); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }
      `}</style>
    </>
  );
};

export default Chatbot; 