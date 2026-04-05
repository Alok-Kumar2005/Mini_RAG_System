"use client";

import React, { useEffect, useState } from 'react';
import { api } from '@/services/api';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { MessageSquarePlus, MessageCircle, LogOut, FileText } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

export interface Chat {
  id: string;
  title: string;
  created_at: string;
  pdf_filename?: string;
}

interface SidebarProps {
  onChatSelected?: (chatId: string) => void;
}

export default function Sidebar({ onChatSelected }: SidebarProps) {
  const [chats, setChats] = useState<Chat[]>([]);
  const pathname = usePathname();
  const router = useRouter();
  const { logout, user } = useAuth();
  const [isCreating, setIsCreating] = useState(false);

  const fetchChats = async () => {
    try {
      const data = await api.get<Chat[]>('/chats');
      setChats(data);
    } catch (err) {
      console.error('Failed to fetch chats:', err);
    }
  };

  useEffect(() => {
    fetchChats();
  }, [pathname]); // Refetch if navigation changes (new chat created)

  const handleNewChat = async () => {
    setIsCreating(true);
    try {
      const newChat = await api.post<Chat>('/chats', { title: 'New Chat' });
      setChats([newChat, ...chats]);
      router.push(`/c/${newChat.id}`);
    } catch (err) {
      console.error(err);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <aside className="sidebar glass-panel">
      <div className="sidebar-header">
        <h2>AI Docs</h2>
        <button 
          className="btn-primary new-chat-btn"
          onClick={handleNewChat}
          disabled={isCreating}
        >
          <MessageSquarePlus size={18} />
          <span>New Chat</span>
        </button>
      </div>

      <div className="chat-list">
        {chats.length === 0 ? (
          <div className="empty-state">No chats yet</div>
        ) : (
          chats.map(chat => {
            const isActive = pathname === `/c/${chat.id}`;
            return (
              <Link 
                href={`/c/${chat.id}`} 
                key={chat.id}
                className={`chat-item ${isActive ? 'active' : ''}`}
              >
                <MessageCircle size={18} className="chat-icon" />
                <div className="chat-info">
                  <span className="chat-title" title={chat.title}>{chat.title}</span>
                  {chat.pdf_filename && (
                    <span className="chat-subtitle">
                      <FileText size={12} /> {chat.pdf_filename}
                    </span>
                  )}
                </div>
              </Link>
            );
          })
        )}
      </div>

      <div className="sidebar-footer">
        <div className="user-info">
          <div className="avatar">{user?.username.charAt(0).toUpperCase()}</div>
          <span>{user?.username}</span>
        </div>
        <button className="btn-icon logout-btn" onClick={logout} title="Log out">
          <LogOut size={18} />
        </button>
      </div>

      <style jsx>{`
        .sidebar {
          width: 300px;
          height: 100vh;
          display: flex;
          flex-direction: column;
          border-radius: 0;
          border-left: none;
          border-top: none;
          border-bottom: none;
        }

        .sidebar-header {
          padding: 1.5rem;
          border-bottom: 1px solid var(--panel-border);
        }

        .sidebar-header h2 {
          font-size: 1.25rem;
          margin-bottom: 1.5rem;
          background: var(--accent-gradient);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .new-chat-btn {
          width: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
        }

        .chat-list {
          flex: 1;
          overflow-y: auto;
          padding: 1rem 0;
        }

        .empty-state {
          color: var(--text-secondary);
          text-align: center;
          padding: 2rem 1rem;
          font-size: 0.9rem;
        }

        .chat-item {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.75rem 1.5rem;
          color: var(--text-secondary);
          transition: all 0.2s ease;
        }

        .chat-item:hover {
          background: rgba(255, 255, 255, 0.05);
          color: var(--text-primary);
        }

        .chat-item.active {
          background: var(--ai-msg-bg);
          color: var(--accent-primary);
          border-right: 3px solid var(--accent-primary);
        }

        .chat-icon {
          flex-shrink: 0;
        }

        .chat-info {
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }

        .chat-title {
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          font-weight: 500;
          font-size: 0.95rem;
        }

        .chat-subtitle {
          font-size: 0.75rem;
          color: var(--text-secondary);
          display: flex;
          align-items: center;
          gap: 0.25rem;
          margin-top: 0.25rem;
        }

        .sidebar-footer {
          padding: 1rem 1.5rem;
          border-top: 1px solid var(--panel-border);
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .user-info {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          font-weight: 500;
        }

        .avatar {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background: var(--accent-gradient);
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: bold;
        }

        .logout-btn:hover {
          color: var(--danger);
          background: rgba(239, 68, 68, 0.1);
        }
      `}</style>
    </aside>
  );
}
