"use client";

import React, { useState, useEffect, useRef, use } from 'react';
import { api } from '@/services/api';
import { Send, FileText, Plus, X, Upload, MessageSquarePlus } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ComponentProps {
  params: Promise<{ id: string }>;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function ChatArea({ params }: ComponentProps) {
  const unwrappedParams = use(params);
  const chatId = unwrappedParams.id;
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [chatInfo, setChatInfo] = useState<any>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamStatus, setStreamStatus] = useState<string | null>(null);

  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchChatData = async () => {
    try {
      const [info, history] = await Promise.all([
        api.get(`/chats/${chatId}`),
        api.get<{ messages: Message[] }>(`/chats/${chatId}/history`)
      ]);
      setChatInfo(info);
      setMessages(history.messages || []);
      scrollToBottom();
    } catch (err) {
      console.error('Failed to load chat data', err);
    }
  };

  useEffect(() => {
    fetchChatData();
  }, [chatId]);

  const scrollToBottom = () => {
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputValue.trim() || isStreaming) return;

    const userMsg: Message = { role: 'user', content: inputValue };
    setMessages((prev) => [...prev, userMsg]);
    setInputValue('');
    setIsStreaming(true);

    // Initial placeholder for assistant message
    setMessages((prev) => [...prev, { role: 'assistant', content: '' }]);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/chats/${chatId}/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ content: userMsg.content }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      if (response.body) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = '';
        
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          // The last element is either an empty string (if ends with newline) or incomplete line
          buffer = lines.pop() || '';
          
          for (const line of lines) {
            if (line.trim() === '') continue;
            if (line.startsWith('data: ')) {
              const dataStr = line.substring(6).trim();
              if (!dataStr || dataStr === '[DONE]') continue;
              
              try {
                const data = JSON.parse(dataStr);
                if (data.type === 'token' && data.content) {
                  setMessages((prev) => {
                    const newMessages = [...prev];
                    const lastIdx = newMessages.length - 1;
                    const lastMsg = newMessages[lastIdx];
                    if (lastMsg && lastMsg.role === 'assistant') {
                      newMessages[lastIdx] = {
                        ...lastMsg,
                        content: lastMsg.content + data.content
                      };
                    }
                    return newMessages;
                  });
                } else if (data.type === 'retry') {
                  // LLM is retrying — clear previous attempt's content so only the final answer shows
                  setMessages((prev) => {
                    const newMessages = [...prev];
                    const lastIdx = newMessages.length - 1;
                    const lastMsg = newMessages[lastIdx];
                    if (lastMsg && lastMsg.role === 'assistant') {
                      newMessages[lastIdx] = { ...lastMsg, content: '' };
                    }
                    return newMessages;
                  });
                  setStreamStatus(`Refining answer (attempt ${data.attempt + 1})…`);
                } else if (data.type === 'status' && data.message) {
                  setStreamStatus(data.message);
                }
              } catch (e) {
                // Ignore incomplete JSON parsing errors
              }
            }
          }
        }
      }
    } catch (err) {
      console.error('Streaming failed:', err);
    } finally {
      setIsStreaming(false);
      setStreamStatus(null);
      
      // The backend might have used an LLM to generate a new chat title on the first message
      // Let's refresh the current header and tell the Sidebar to refresh too!
      fetchChatData();
      window.dispatchEvent(new Event('chatUpdated'));
    }
  };

  const handleUploadFile = async () => {
    if (!file) return;
    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      await api.post(`/chats/${chatId}/upload`, formData);
      setShowUploadModal(false);
      setFile(null);
      // Refresh chat info to see the new PDF title
      fetchChatData();
    } catch (err) {
      console.error('Upload failed:', err);
      alert('Upload failed. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header glass-panel">
        <div className="chat-title-area">
          <h3>{chatInfo?.title || 'Loading...'}</h3>
          {chatInfo?.pdf_filename && (
            <span className="pdf-badge">
              <FileText size={14} /> {chatInfo.pdf_filename}
            </span>
          )}
        </div>
      </div>

      <div className="messages-area">
        
        {messages.length === 0 ? (
          <div className="empty-chat-state">
            <div className="empty-chat-icon">
              <MessageSquarePlus size={40} />
            </div>
            <h2>Start a conversation</h2>
            <p>Upload a document using the + button to enable context-aware capabilities.</p>
          </div>
        ) : (
          messages.filter((msg, idx) => {
            if (msg.role === 'user') return true;
            if (isStreaming && idx === messages.length - 1) return true;
            if (msg.content && msg.content.trim() !== '') return true;
            return false;
          }).map((msg, idx, filteredArr) => {
            const isLastAssistant = msg === filteredArr[filteredArr.length - 1] && msg.role === 'assistant';
            const showStatus = isLastAssistant && isStreaming && (!msg.content || streamStatus);
            
            return (
              <div key={idx} className={`message-row ${msg.role}`}>
                <div className={`message-bubble ${msg.role} ${showStatus && !msg.content && !streamStatus ? 'streaming-indicator' : ''}`}>
                  {msg.role === 'assistant' ? (
                    <div className="markdown-body">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    msg.content
                  )}
                  {showStatus && !msg.content && (
                    streamStatus ? (
                      <span className="status-text">{streamStatus}</span>
                    ) : (
                      <><span className="dot"></span><span className="dot"></span><span className="dot"></span></>
                    )
                  )}
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="composer-area glass-panel">
        <form className="composer-form" onSubmit={handleSendMessage}>
          <button 
            type="button" 
            className="btn-icon upload-trigger-btn"
            onClick={() => setShowUploadModal(true)}
            title="Upload Document"
          >
            <Plus size={24} />
          </button>
          
          <input
            type="text"
            className="input-field composer-input"
            placeholder="Message Document AI..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isStreaming}
          />
          
          <button 
            type="submit" 
            className="btn-icon send-btn"
            disabled={!inputValue.trim() || isStreaming}
          >
            <Send size={20} />
          </button>
        </form>
      </div>

      {showUploadModal && (
        <div className="modal-overlay">
          <div className="modal-content glass-panel animate-fade-in">
            <button className="close-btn" onClick={() => {
              setShowUploadModal(false);
              setFile(null);
            }}>
              <X size={20} />
            </button>
            
            <h3 className="modal-title">Upload Document</h3>
            <p className="modal-subtitle">Add a PDF file to give the AI context for this chat.</p>
            
            <div className="upload-box" onClick={() => fileInputRef.current?.click()}>
              <input 
                type="file" 
                accept=".pdf" 
                ref={fileInputRef}
                style={{ display: 'none' }}
                onChange={(e) => {
                  if (e.target.files && e.target.files.length > 0) {
                    setFile(e.target.files[0]);
                  }
                }}
              />
              <Upload size={32} className="upload-icon" />
              <p>Click to select or drag and drop</p>
              <span className="file-format">PDF up to 10MB</span>
              
              {file && (
                <div className="selected-file">
                  <FileText size={16} />
                  <span>{file.name}</span>
                </div>
              )}
            </div>
            
            <button 
              className="btn-primary w-full" 
              disabled={!file || isUploading}
              onClick={handleUploadFile}
            >
              {isUploading ? <div className="loader inline-loader"></div> : 'Confirm Upload'}
            </button>
          </div>
        </div>
      )}

      <style jsx>{`
        .chat-container {
          display: flex;
          flex-direction: column;
          height: 100vh;
          width: 100%;
          background: var(--bg-color);
        }

        .chat-header {
          padding: 1rem 1.5rem;
          border-radius: 0;
          border-top: none;
          border-left: none;
          border-right: none;
          z-index: 10;
        }

        .chat-title-area {
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
        }

        .pdf-badge {
          display: inline-flex;
          align-items: center;
          gap: 0.25rem;
          font-size: 0.75rem;
          color: var(--accent-primary);
          background: rgba(59, 130, 246, 0.1);
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
          width: max-content;
        }

        .messages-area {
          flex: 1;
          overflow-y: auto;
          padding: 1.5rem;
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .empty-chat-state {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          color: var(--text-secondary);
          text-align: center;
        }

        .empty-chat-icon {
          width: 80px;
          height: 80px;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.05);
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 1.5rem;
        }

        .message-row {
          display: flex;
          width: 100%;
        }

        .message-row.user {
          justify-content: flex-end;
        }

        .message-row.assistant {
          justify-content: flex-start;
        }

        .message-bubble {
          max-width: 75%;
          padding: 1rem;
          border-radius: 12px;
          line-height: 1.5;
          word-wrap: break-word;
          white-space: pre-wrap;
        }

        .message-bubble.user {
          background: var(--user-msg-bg);
          border: 1px solid var(--panel-border);
          border-bottom-right-radius: 4px;
        }

        .message-bubble.assistant {
          background: var(--ai-msg-bg);
          border: 1px solid rgba(59, 130, 246, 0.2);
          border-bottom-left-radius: 4px;
          position: relative;
        }

        .composer-area {
          padding: 1rem 1.5rem;
          border-radius: 0;
          border-bottom: none;
          border-left: none;
          border-right: none;
        }

        .composer-form {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .upload-trigger-btn {
          background: rgba(255, 255, 255, 0.05);
          flex-shrink: 0;
        }
        
        .upload-trigger-btn:hover {
          color: var(--accent-primary);
        }

        .composer-input {
          flex: 1;
          border-radius: 20px;
          background: rgba(0, 0, 0, 0.3);
        }

        .send-btn {
          background: var(--accent-gradient);
          color: white;
          flex-shrink: 0;
        }

        .send-btn:hover:not(:disabled) {
          box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        }

        .send-btn:disabled {
          background: rgba(255, 255, 255, 0.1);
          color: var(--text-secondary);
        }

        /* Modal Styles */
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.6);
          backdrop-filter: blur(4px);
          z-index: 100;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 1rem;
        }

        .modal-content {
          width: 100%;
          max-width: 450px;
          padding: 2rem;
          position: relative;
        }

        .close-btn {
          position: absolute;
          top: 1rem;
          right: 1rem;
          background: transparent;
          border: none;
          color: var(--text-secondary);
          cursor: pointer;
        }

        .close-btn:hover {
          color: var(--text-primary);
        }

        .modal-title {
          font-size: 1.5rem;
          margin-bottom: 0.5rem;
        }

        .modal-subtitle {
          color: var(--text-secondary);
          margin-bottom: 1.5rem;
          font-size: 0.9rem;
        }

        .upload-box {
          border: 2px dashed var(--panel-border);
          border-radius: 12px;
          padding: 2rem;
          text-align: center;
          cursor: pointer;
          transition: all 0.2s ease;
          margin-bottom: 1.5rem;
          background: rgba(0, 0, 0, 0.2);
        }

        .upload-box:hover {
          border-color: var(--accent-primary);
          background: rgba(59, 130, 246, 0.05);
        }

        .upload-icon {
          color: var(--accent-primary);
          margin-bottom: 1rem;
        }

        .file-format {
          display: block;
          font-size: 0.75rem;
          color: var(--text-secondary);
          margin-top: 0.5rem;
        }

        .selected-file {
          margin-top: 1rem;
          padding: 0.5rem;
          background: rgba(59, 130, 246, 0.1);
          border-radius: 6px;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
          color: var(--accent-primary);
          font-weight: 500;
        }

        .w-full {
          width: 100%;
        }

        /* Streaming Indicator */
        .streaming-indicator .dot {
          display: inline-block;
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: var(--accent-primary);
          margin: 0 2px;
          animation: wave 1.3s linear infinite;
        }

        .streaming-indicator .dot:nth-child(2) {
          animation-delay: -1.1s;
        }

        .streaming-indicator .dot:nth-child(3) {
          animation-delay: -0.9s;
        }

        @keyframes wave {
          0%, 60%, 100% {
            transform: initial;
            opacity: 0.4;
          }
          30% {
            transform: translateY(-4px);
            opacity: 1;
          }
        }

        .status-text {
          color: var(--accent-primary);
          font-style: italic;
          font-size: 0.95rem;
          animation: pulseStatus 1.5s ease-in-out infinite;
        }

        @keyframes pulseStatus {
          0%, 100% { opacity: 0.6; }
          50% { opacity: 1; }
        }

        .markdown-body {
          font-family: inherit;
        }
        
        .markdown-body p {
          margin-bottom: 0.75rem;
        }
        
        .markdown-body p:last-child {
          margin-bottom: 0;
        }

        .markdown-body table {
          width: 100%;
          border-collapse: collapse;
          margin: 1rem 0;
          font-size: 0.9em;
        }

        .markdown-body th, .markdown-body td {
          border: 1px solid var(--panel-border);
          padding: 8px 12px;
          text-align: left;
        }

        .markdown-body th {
          background-color: rgba(255, 255, 255, 0.05);
          font-weight: 600;
        }

        .markdown-body strong {
          color: var(--text-primary);
          font-weight: 700;
        }

        .markdown-body ul, .markdown-body ol {
          margin-left: 1.5rem;
          margin-bottom: 1rem;
        }

        .markdown-body code {
          background-color: rgba(0, 0, 0, 0.3);
          padding: 2px 4px;
          border-radius: 4px;
          font-family: monospace;
          font-size: 0.9em;
        }

        .markdown-body pre {
          background-color: rgba(0, 0, 0, 0.3);
          padding: 1rem;
          border-radius: 8px;
          overflow-x: auto;
          margin-bottom: 1rem;
        }
        
        .markdown-body pre code {
          background-color: transparent;
          padding: 0;
        }


      `}</style>
    </div>
  );
}
