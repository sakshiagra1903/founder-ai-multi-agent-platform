const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

class ApiService {
  private getHeaders(contentType: string | null = 'application/json'): HeadersInit {
    const headers: HeadersInit = {};
    if (contentType) {
      headers['Content-Type'] = contentType;
    }
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      let errorMessage = 'An error occurred';
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorMessage;
      } catch {
        errorMessage = response.statusText || errorMessage;
      }
      throw new Error(errorMessage);
    }
    return response.json() as Promise<T>;
  }

  // Auth Operations
  async signup(name: string, email: string, password: string): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/auth/signup`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ name, email, password }),
    });
    return this.handleResponse(res);
  }

  async login(email: string, password: string): Promise<{ access_token: string; token_type: string }> {
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ email, password }),
    });
    return this.handleResponse(res);
  }

  // Document Operations
  async listDocuments(): Promise<any[]> {
    const res = await fetch(`${API_BASE_URL}/documents`, {
      method: 'GET',
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  async uploadDocument(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_BASE_URL}/documents/upload`, {
      method: 'POST',
      headers: this.getHeaders(null), // fetch will auto-set the boundary for multipart
      body: formData,
    });
    return this.handleResponse(res);
  }

  async deleteDocument(id: string): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/documents/${id}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  // Chat Operations
  async askQuestion(question: string): Promise<{ answer: string; sources: any[]; ticket?: any }> {
    const res = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ question }),
    });
    return this.handleResponse(res);
  }

  async getChatHistory(): Promise<any[]> {
    const res = await fetch(`${API_BASE_URL}/chat/history`, {
      method: 'GET',
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }

  // Streams the agentic RAG pipeline over SSE (POST /chat/stream).
  // Calls `onEvent` for every parsed event as it arrives from the server.
  async streamQuestion(
    question: string,
    onEvent: (event: any) => void,
    signal?: AbortSignal
  ): Promise<void> {
    const res = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ question }),
      signal,
    });

    if (!res.ok || !res.body) {
      let errorMessage = 'Failed to start streaming response';
      try {
        const errorData = await res.json();
        errorMessage = errorData.detail || errorMessage;
      } catch {
        errorMessage = res.statusText || errorMessage;
      }
      throw new Error(errorMessage);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      // SSE events are separated by a blank line
      const parts = buffer.split('\n\n');
      buffer = parts.pop() || '';

      for (const part of parts) {
        const line = part.trim();
        if (!line.startsWith('data:')) continue;
        const jsonStr = line.slice(5).trim();
        if (!jsonStr) continue;
        try {
          onEvent(JSON.parse(jsonStr));
        } catch (e) {
          console.error('Failed to parse SSE event:', jsonStr, e);
        }
      }
    }
  }

  // Ticket Operations
  async getTickets(): Promise<any[]> {
    const res = await fetch(`${API_BASE_URL}/tickets`, {
      method: 'GET',
      headers: this.getHeaders(),
    });
    return this.handleResponse(res);
  }
}

export const apiService = new ApiService();
