"use client";

import React, { useEffect, useState } from 'react';
import { api } from '@/services/api';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { MessageSquarePlus, MessageCircle, LogOut, FileText, MoreVertical, Pencil, Trash2 } from 'lucide-react';
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
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if ((e.target as Element).closest('.chat-actions-container')) {
        return;
      }
      setActiveDropdown(null);
    };
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

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
    const handleUpdate = () => fetchChats();
    window.addEventListener('chatUpdated', handleUpdate);
    return () => window.removeEventListener('chatUpdated', handleUpdate);
  }, [pathname]); // Refetch if navigation changes or if explicitly triggered

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

  const handleRename = async (chatId: string, oldTitle: string) => {
    setActiveDropdown(null);
    const newTitle = prompt('Enter new chat title:', oldTitle);
    if (!newTitle || newTitle === oldTitle) return;

    try {
      await api.patch(`/chats/${chatId}/rename`, { title: newTitle });
      setChats(prev => prev.map(c => c.id === chatId ? { ...c, title: newTitle } : c));
    } catch (err) {
      console.error('Failed to rename chat:', err);
      alert('Failed to rename chat');
    }
  };

  const handleDelete = async (chatId: string) => {
    setActiveDropdown(null);
    if (!confirm('Are you sure you want to delete this chat?')) return;

    try {
      await api.delete(`/chats/${chatId}`);
      setChats(prev => prev.filter(c => c.id !== chatId));
      if (pathname === `/c/${chatId}`) {
        router.push('/');
      }
    } catch (err) {
      console.error('Failed to delete chat:', err);
      alert('Failed to delete chat');
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
              <div key={chat.id} className={`chat-item ${isActive ? 'active' : ''}`}>
                <Link 
                  href={`/c/${chat.id}`} 
                  className="chat-link"
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
                
                <div className="chat-actions-container">
                  <button 
                    className="btn-icon action-trigger"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      setActiveDropdown(activeDropdown === chat.id ? null : chat.id);
                    }}
                  >
                    <MoreVertical size={16} />
                  </button>
                  
                  {activeDropdown === chat.id && (
                    <div className="dropdown-menu glass-panel animate-fade-in" onClick={e => e.stopPropagation()}>
                      <button className="dropdown-item" onClick={(e) => { e.preventDefault(); handleRename(chat.id, chat.title); }}>
                        <Pencil size={14} /> <span>Rename</span>
                      </button>
                      <button className="dropdown-item danger" onClick={(e) => { e.preventDefault(); handleDelete(chat.id); }}>
                        <Trash2 size={14} /> <span>Delete</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
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
          justify-content: space-between;
          padding: 0.5rem 0.5rem 0.5rem 1rem;
          color: var(--text-secondary);
          transition: all 0.2s ease;
          position: relative;
        }

        .chat-link {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          flex: 1;
          min-width: 0;
          color: inherit;
          text-decoration: none;
          padding: 0.25rem 0;
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
          flex: 1;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          min-width: 0;
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

        .chat-actions-container {
          position: relative;
          flex-shrink: 0;
          margin-left: 0.5rem;
        }

        .action-trigger {
          width: 28px;
          height: 28px;
          opacity: 0.4;
          transition: opacity 0.2s ease, background 0.2s ease, color 0.2s ease;
        }

        .chat-item:hover .action-trigger, .action-trigger:focus {
          opacity: 1;
        }

        .dropdown-menu {
          position: absolute;
          top: 100%;
          right: 0;
          z-index: 9999;
          min-width: 140px;
          padding: 0.5rem;
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
          margin-top: 0.25rem;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        }

        .dropdown-item {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          width: 100%;
          padding: 0.5rem 0.75rem;
          border: none;
          background: transparent;
          color: var(--text-primary);
          border-radius: 6px;
          font-family: inherit;
          cursor: pointer;
          transition: background 0.2s ease;
          font-size: 0.85rem;
          text-align: left;
        }

        .dropdown-item:hover {
          background: rgba(255, 255, 255, 0.1);
        }

        .dropdown-item.danger {
          color: var(--danger);
        }

        .dropdown-item.danger:hover {
          background: rgba(239, 68, 68, 0.1);
        }
      `}</style>
    </aside>
  );
}
