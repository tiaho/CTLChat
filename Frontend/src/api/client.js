import axios from "axios";

const API_BASE_URL = "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Interceptor to handle FormData
api.interceptors.request.use((config) => {
  // If data is FormData, remove Content-Type to let browser set it with boundary
  if (config.data instanceof FormData) {
    delete config.headers['Content-Type'];
  }
  return config;
});

export const apiClient = {
  // Health check
  health: () => api.get("/health"),

  // Get statistics
  getStats: () => api.get("/stats"),

  // Chat endpoints
  chat: (query, conversationHistory = null, topK = null) =>
    api.post("/chat", {
      query,
      conversation_history: conversationHistory,
      top_k: topK,
      stream: false,
    }),

  // Streaming chat endpoint
  chatStream: async (query, conversationHistory = null, topK = null, onChunk) => {
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        conversation_history: conversationHistory,
        top_k: topK,
        stream: true,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullResponse = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      fullResponse += chunk;
      if (onChunk) {
        onChunk(chunk);
      }
    }

    return fullResponse;
  },

  // File upload endpoint
  uploadFile: (file, userId = null, orgId = null, visibility = "personal") => {
    const formData = new FormData();
    formData.append("file", file);
    if (userId) formData.append("user_id", userId);
    if (orgId) formData.append("org_id", orgId);
    formData.append("visibility", visibility);

    return api.post("/upload", formData);
  },
};

export default api;
