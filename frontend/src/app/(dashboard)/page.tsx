"use client";

import React from 'react';
import { MessageSquarePlus } from 'lucide-react';

export default function DashboardHome() {
  return (
    <div className="empty-dashboard">
      <div className="glass-panel welcome-panel animate-fade-in">
        <div className="icon-container">
          <MessageSquarePlus size={48} className="text-accent" />
        </div>
        <h1>Welcome to AI Document Chat</h1>
        <p>Select an existing chat from the sidebar, or create a new one to start analyzing documents.</p>
      </div>

      <style jsx>{`
        .empty-dashboard {
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 2rem;
        }

        .welcome-panel {
          width: 100%;
          max-width: 600px;
          padding: 4rem 2rem;
          text-align: center;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 1.5rem;
        }

        .icon-container {
          width: 96px;
          height: 96px;
          border-radius: 50%;
          background: var(--ai-msg-bg);
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--accent-primary);
        }

        .welcome-panel h1 {
          font-size: 2rem;
          background: var(--accent-gradient);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          margin: 0;
        }

        .welcome-panel p {
          color: var(--text-secondary);
          font-size: 1.1rem;
          max-width: 400px;
        }
      `}</style>
    </div>
  );
}
