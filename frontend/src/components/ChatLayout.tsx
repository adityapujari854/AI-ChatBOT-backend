"use client";

import { useState, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";
import Sidebar from "./Sidebar";
import ChatInput from "./ChatInput";
import { Menu } from "lucide-react";
import "../styles/chatLayout.css";

export type SessionType = {
  id: string;
  title: string;
  messages: { user: string; ai: string }[];
};

interface ChatLayoutProps {
  children: React.ReactNode;
  sessions: SessionType[];
  chatHistory: { user: string; ai: string }[];
  onSelectSession: (sessionId: string) => void;
  onNewSession: () => void;
  onSubmitMessage: (message: string) => void;
}

export default function ChatLayout({
  children,
  sessions,
  chatHistory,
  onSelectSession,
  onNewSession,
  onSubmitMessage,
}: ChatLayoutProps) {
  const [activeSessionIndex, setActiveSessionIndex] = useState<number | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);

  const handleSessionSelect = (sessionId: string) => {
    const selectedIndex = sessions.findIndex((session) => session.id === sessionId);
    setActiveSessionIndex(selectedIndex);
    onSelectSession(sessionId);
    if (window.innerWidth < 768) setSidebarOpen(false);
  };

  useEffect(() => {
    if (sessions.length > 0 && activeSessionIndex === null) {
      setActiveSessionIndex(0);
    }
  }, [sessions]);

  return (
    <div className="chat-layout min-h-screen flex flex-col md:flex-row relative overflow-hidden">
      {/* Sidebar toggle button */}
      <button
        className="absolute top-4 left-4 z-50 bg-blue-600 text-white p-2 rounded-md md:hidden"
        onClick={() => setSidebarOpen(!sidebarOpen)}
        aria-label="Toggle sidebar"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Sidebar */}
      <div className={`${sidebarOpen ? "sidebar" : "sidebar sidebar-hidden"} md:relative`}>
        <Sidebar
          sessions={sessions}
          chatHistory={chatHistory}
          onSelectSession={handleSessionSelect}
          onNewSession={onNewSession}
        />
      </div>

      {/* Chat Content */}
      <div className="chat-content flex-1 flex flex-col relative overflow-hidden">
        <div className="chat-main flex-1 overflow-y-auto pb-24 px-4">
          {children}
        </div>
        <ChatInput onSubmit={onSubmitMessage} />
      </div>
    </div>
  );
}
