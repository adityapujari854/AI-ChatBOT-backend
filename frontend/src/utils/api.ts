import axios from 'axios';

const backendURL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

/**
 * Send a message to the backend and receive AI response.
 */
export const sendMessageToBackend = async (
  message: string,
  sessionId: string,
  userId: string,
  language: string = 'en'
): Promise<string> => {
  try {
    // Send POST request to the backend chat endpoint
    const response = await axios.post(`${backendURL}/api/chat`, {
      prompt: message,
      language: language,
      session_id: sessionId,
      user_id: userId, // Make sure to send user_id as per the backend model
    });

    return response.data.response || 'No response from backend.';
  } catch (error) {
    console.error('Error sending message to backend:', error);
    return 'Sorry, something went wrong. Please try again later.';
  }
};

/**
 * Fetch chat history for a specific session.
 */
export const fetchChatHistory = async (
  sessionId: string
): Promise<{ user: string; ai: string }[]> => {
  try {
    // Send GET request to fetch chat history
    const response = await axios.get(`${backendURL}/api/chat/history`, {
      params: { session_id: sessionId }, // Ensure correct parameter is passed
    });

    return response.data.history || [];
  } catch (error) {
    console.error('Error fetching chat history:', error);
    return [];
  }
};

/**
 * Fetch list of all sessions for a specific user.
 */
export const fetchSessions = async (userId: string): Promise<{
  id: string;
  title: string;
  created_at: string;
}[]> => {
  try {
    // Send GET request to fetch all sessions for the specific user
    const response = await axios.get(`${backendURL}/api/chat/sessions`, {
      params: { user_id: userId }, // Make sure to pass user_id to filter sessions
    });

    return response.data.sessions || [];
  } catch (error) {
    console.error('Error fetching sessions:', error);
    return [];
  }
};
