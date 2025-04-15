"use client";

import { useState, useRef, useEffect } from "react";

interface ChatInputProps {
  onSubmit: (message: string) => void;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSubmit }) => {
  const [input, setInput] = useState<string>("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      onSubmit(input);
      setInput("");
    }
  };

  // Auto-focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  return (
    <form
      onSubmit={handleSubmit}
      className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 px-4 py-3 z-20"
    >
      <div className="mx-auto flex w-full max-w-3xl items-center gap-3">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask something..."
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          Send
        </button>
      </div>
    </form>
  );
};

export default ChatInput;
