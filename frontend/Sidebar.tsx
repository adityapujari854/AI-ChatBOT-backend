"use client";
import { useState, useEffect } from "react";
import { Menu, X } from "lucide-react"; // optional icons for toggle button
import "../styles/chatLayout.css";

interface Session {
  id: string;
  title: string;
  created_at?: string;
}

interface SidebarProps {
  onSelectSession: (sessionId: string) => void;
  onNewSession: () => void;
  sessions: Session[];
  chatHistory: any[];
}

const Sidebar = ({ sessions, chatHistory, onSelectSession, onNewSession }: SidebarProps) => {
  const [isOpen, setIsOpen] = useState(true);

  const toggleSidebar = () => {
    setIsOpen((prev) => !prev);
  };

  return (
    <>
      {/* Sidebar */}
      <aside
        className={`sidebar transition-transform duration-300 ease-in-out ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        } md:translate-x-0 md:static fixed top-0 left-0 h-full z-40 bg-gray-100 border-r shadow-md w-64 p-4 overflow-y-auto`}
      >
        <button
          onClick={onNewSession}
          className="new-session-btn"
        >
          + New Chat
        </button>

        {/* Chat History Section */}
        {chatHistory.length > 0 && (
          <>
            <h2 className="section-header">Recent Prompts</h2>
            <ul className="session-list">
              {chatHistory.map((chat: any) => (
                <li key={chat.id}>
                  <button
                    onClick={() => onSelectSession(chat.id)}
                    className="session-btn"
                  >
                    {chat.user_prompt || `Chat ${chat.title}`}
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}

        {/* Sessions Section */}
        {sessions.length > 0 && (
          <>
            <h2 className="section-header mt-6">Sessions</h2>
            <ul className="session-list">
              {sessions.map((session) => (
                <li key={session.id}>
                  <button
                    onClick={() => onSelectSession(session.id)}
                    className="session-btn"
                  >
                    {session.title || `Untitled Chat`}
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}
      </aside>
    </>
  );
};

export default Sidebar;
