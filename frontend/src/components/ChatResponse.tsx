import { useState, useEffect } from 'react';
import { sendMessageToBackend } from '../utils/api';
import ChatInput from '../components/ChatInput';
import { v4 as uuidv4 } from 'uuid';
import DOMPurify from 'dompurify';

const ChatResponse = () => {
  const [response, setResponse] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [chatHistory, setChatHistory] = useState<{ user: string; ai: string }[]>([]);
  const [sessionId, setSessionId] = useState<string>('');
  const [userId, setUserId] = useState<string>('');

  useEffect(() => {
    const storedUserId = localStorage.getItem('user_id');
    if (!storedUserId) {
      const newUserId = uuidv4();
      localStorage.setItem('user_id', newUserId);
      setUserId(newUserId);
    } else {
      setUserId(storedUserId);
    }

    const newSessionId = `session-${Date.now()}`;
    setSessionId(newSessionId);
  }, []);

  const handleSubmit = async (message: string) => {
    if (!message.trim()) return;
    setIsLoading(true);
    try {
      const aiResponse = await sendMessageToBackend(message, sessionId, userId);
      const sanitizedResponse = DOMPurify.sanitize(aiResponse);
      setChatHistory((prev) => [...prev, { user: message, ai: sanitizedResponse }]);
      setResponse(sanitizedResponse);
    } catch (error) {
      setResponse('Failed to connect to backend.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-2xl mx-auto bg-white p-8 rounded-xl shadow-md">
        <h1 className="text-3xl font-bold text-blue-600 mb-4 text-center">
          🤖 My AI Assistant
        </h1>
        <ChatInput onSubmit={handleSubmit} />
        {isLoading && (
          <p className="text-center mt-4 text-sm text-gray-500">Thinking...</p>
        )}
        <div className="mt-6 space-y-4">
          {chatHistory.map((entry, idx) => (
            <div key={idx} className="bg-gray-50 p-4 rounded-md shadow-sm">
              <p className="font-semibold text-gray-800">You: {entry.user}</p>
              <div
                className="text-gray-700 mt-1 space-y-2 prose prose-sm max-w-none"
                dangerouslySetInnerHTML={{ __html: entry.ai }}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ChatResponse;
