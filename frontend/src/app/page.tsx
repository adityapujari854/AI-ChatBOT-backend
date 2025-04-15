"use client";

import { useState, useEffect } from "react";
import ChatLayout from "../components/ChatLayout";
import {
  sendMessageToBackend,
  fetchChatHistory,
  fetchSessions,
} from "../utils/api";
import "bootstrap/dist/css/bootstrap.min.css";
import { v4 as uuidv4 } from "uuid";
import "../styles/globals.css";

const Home = () => {
  const [chatHistory, setChatHistory] = useState<{ user: string; ai: string }[]>(
    []
  );
  const [isLoading, setIsLoading] = useState(false);
  const [currentTypedText, setCurrentTypedText] = useState("");
  const [fullResponse, setFullResponse] = useState("");
  const [sessions, setSessions] = useState<any[]>([]);
  const [selectedSessionIndex, setSelectedSessionIndex] = useState<number | null>(
    null
  );
  const [sessionId, setSessionId] = useState("");
  const [userId, setUserId] = useState("");

  useEffect(() => {
    const storedUserId = localStorage.getItem("user_id");
    if (!storedUserId) {
      const newUserId = uuidv4();
      localStorage.setItem("user_id", newUserId);
      setUserId(newUserId);
    } else {
      setUserId(storedUserId);
    }
  }, []);

  useEffect(() => {
    const storedSessionId = localStorage.getItem("session_id");
    if (!storedSessionId) {
      const newSessionId = uuidv4();
      localStorage.setItem("session_id", newSessionId);
      setSessionId(newSessionId);
    } else {
      setSessionId(storedSessionId);
    }
  }, []);

  useEffect(() => {
    const loadSessions = async () => {
      if (userId) {
        try {
          const userSessions = await fetchSessions(userId);
          setSessions(userSessions);
        } catch (error) {
          console.error("Failed to fetch sessions:", error);
        }
      }
    };
    loadSessions();
  }, [userId]);

  useEffect(() => {
    const loadChatHistory = async () => {
      if (sessionId) {
        try {
          const history = await fetchChatHistory(sessionId);
          setChatHistory(history);
        } catch (error) {
          console.error("Failed to fetch chat history:", error);
        }
      }
    };
    loadChatHistory();
  }, [sessionId]);

  const handleSubmit = async (message: string) => {
    if (!message.trim() || !sessionId) return;

    setIsLoading(true);
    setCurrentTypedText("");
    setFullResponse("");

    try {
      setChatHistory((prev) => [...prev, { user: message, ai: "" }]);
      const aiResponse = await sendMessageToBackend(message, sessionId, userId);
      setFullResponse(aiResponse);
    } catch (error) {
      setFullResponse("⚠️ Failed to connect to backend.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!fullResponse) return;

    let i = 0;
    const chunkSize = 40;
    const interval = setInterval(() => {
      setCurrentTypedText((prev) =>
        prev + fullResponse.slice(i, i + chunkSize)
      );
      i += chunkSize;

      if (i >= fullResponse.length) {
        clearInterval(interval);
        setChatHistory((prev) => {
          const updated = [...prev];
          updated[updated.length - 1].ai = fullResponse;
          return updated;
        });
        setFullResponse("");
      }
    }, 60);

    return () => clearInterval(interval);
  }, [fullResponse]);

  const handleSelectSession = (sessionId: string) => {
    setSessionId(sessionId);
    localStorage.setItem("session_id", sessionId);
    const selectedSession = sessions.find((session) => session.id === sessionId);
    if (selectedSession) {
      setChatHistory(selectedSession.messages);
    }
  };

  const handleNewSession = () => {
    const newSessionId = uuidv4();
    setSessionId(newSessionId);
    localStorage.setItem("session_id", newSessionId);
    setChatHistory([]);
    setSelectedSessionIndex(null);
  };

  return (
    <ChatLayout
      sessions={sessions}
      chatHistory={chatHistory}
      onSelectSession={handleSelectSession}
      onNewSession={handleNewSession}
      onSubmitMessage={handleSubmit}
    >
      <div className="chat-main container" style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
        <div className="chat-header">🤖 MY AI ASSISTANT</div>

        <div
          className="chat-box flex-grow"
          style={{ overflowY: "auto", flex: "1" }}
        >
          {chatHistory.map((entry, idx) => (
            <div
              key={idx}
              className={`chat-entry ${idx % 2 === 0 ? "user" : "ai"}`}
            >
              <div className="message-text fw-bold text-dark">{entry.user}</div>
              <div className="message-text text-muted">
                <div
                  dangerouslySetInnerHTML={{
                    __html:
                      idx === chatHistory.length - 1 && fullResponse
                        ? currentTypedText
                        : entry.ai,
                  }}
                />
                {idx === chatHistory.length - 1 && fullResponse && (
                  <span className="animate-pulse">|</span>
                )}
              </div>
            </div>
          ))}
        </div>

        {isLoading && (
          <p className="text-center text-sm text-secondary mt-2">
            💬 Thinking...
          </p>
        )}
      </div>
    </ChatLayout>
  );
};

export default Home;
