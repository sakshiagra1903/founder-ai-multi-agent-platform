'use client';

import { useState, useEffect, useRef } from 'react';
import { apiService } from '@/services/api';
import { ChatMessage, SourceCitation, AgentActivity, TicketInfo } from '@/types';

const TOOL_LABELS: Record<string, string> = {
  search_knowledge_base: 'Searching your documents…',
  web_search: 'Searching the web…',
  create_support_ticket: 'Creating a support ticket…',
};

const TOOL_LABELS_DONE: Record<string, string> = {
  search_knowledge_base: 'Searched your documents',
  web_search: 'Searched the web',
  create_support_ticket: 'Support ticket created',
};

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Citations details panel state
  const [activeCitations, setActiveCitations] = useState<SourceCitation[] | null>(null);
  const [citationsFileName, setCitationsFileName] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load chat history on mount
  useEffect(() => {
    fetchHistory();
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const fetchHistory = async () => {
    try {
      const historyData = await apiService.getChatHistory();
      
      // Transform backend records to front-end messages
      // Backend: [{id, question, answer, sources, timestamp}]
      const parsedMessages: ChatMessage[] = [];
      
      // Order: oldest to newest
      const sortedHistory = [...historyData].reverse();
      
      sortedHistory.forEach((item) => {
        parsedMessages.push({
          id: `${item.id}-q`,
          role: 'user',
          content: item.question,
          timestamp: new Date(item.timestamp)
        });
        parsedMessages.push({
          id: `${item.id}-a`,
          role: 'assistant',
          content: item.answer,
          sources: item.sources || undefined,
          timestamp: new Date(item.timestamp)
        });
      });
      
      setMessages(parsedMessages);
    } catch (err: any) {
      console.error('Failed to load chat history:', err);
    }
  };

  const handleSendMessage = async (e?: React.FormEvent, customText?: string) => {
    e?.preventDefault();
    const queryText = customText || input;
    if (!queryText.trim() || loading) return;

    setError(null);
    setInput('');

    // Add user message to UI
    const userMsg: ChatMessage = {
      id: Math.random().toString(),
      role: 'user',
      content: queryText,
      timestamp: new Date()
    };

    // Add a placeholder assistant message that streams in live
    const agentMsgId = Math.random().toString();
    const agentMsg: ChatMessage = {
      id: agentMsgId,
      role: 'assistant',
      content: '',
      activities: [],
      isStreaming: true,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMsg, agentMsg]);
    setLoading(true);

    const updateAgentMsg = (updater: (msg: ChatMessage) => ChatMessage) => {
      setMessages(prev => prev.map(m => (m.id === agentMsgId ? updater(m) : m)));
    };

    try {
      await apiService.streamQuestion(queryText, (event) => {
        switch (event.type) {
          case 'tool_start': {
            const label = TOOL_LABELS[event.tool] || `Using ${event.tool}…`;
            updateAgentMsg(m => {
              const activities: AgentActivity[] = [
                ...(m.activities || []),
                { tool: event.tool, label, status: 'running' },
              ];
              return { ...m, activities };
            });
            break;
          }
          case 'tool_end': {
            updateAgentMsg(m => {
              const activities = (m.activities || []).map(a =>
                a.tool === event.tool && a.status === 'running'
                  ? { ...a, status: 'done' as const, label: TOOL_LABELS_DONE[a.tool] || a.label }
                  : a
              );
              return { ...m, activities };
            });
            break;
          }
          case 'token': {
            updateAgentMsg(m => ({ ...m, content: m.content + event.content }));
            break;
          }
          case 'sources': {
            const sources: SourceCitation[] = event.sources || [];
            updateAgentMsg(m => ({ ...m, sources }));
            break;
          }
          case 'ticket': {
            const ticket: TicketInfo = event.ticket;
            updateAgentMsg(m => ({ ...m, ticket }));
            break;
          }
          case 'error': {
            setError(event.message || 'An error occurred while generating a response.');
            break;
          }
          case 'done': {
            updateAgentMsg(m => ({
              ...m,
              content: m.content || event.answer || '',
              isStreaming: false,
            }));
            break;
          }
        }
      });
    } catch (err: any) {
      setError(err.message || 'An error occurred while generating a response.');
      updateAgentMsg(m => ({ ...m, isStreaming: false }));
    } finally {
      setLoading(false);
    }
  };

  const handleCitationClick = (citations: SourceCitation[], msgContent: string) => {
    setActiveCitations(citations);
    setCitationsFileName(msgContent.length > 30 ? msgContent.substring(0, 30) + '...' : msgContent);
  };

  // Pre-populated starter prompts
  const starterPrompts = [
    "What is the company password policy?",
    "How does the developer onboarding process work?",
    "What is our startup equity distribution strategy?",
  ];

  return (
    <div className="flex flex-1 h-[calc(100vh-4rem)] bg-slate-50 relative">
      {/* Primary Chat Window */}
      <div className="flex-1 flex flex-col min-w-0 bg-slate-50">
        {/* Messages Stream */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
          {messages.length === 0 && !loading ? (
            <div className="max-w-2xl mx-auto py-16 text-center space-y-8 animate-fade-in">
              <div className="flex flex-col items-center">
                <span className="text-4xl mb-4">🤖</span>
                <h3 className="text-lg font-black text-slate-900 mb-1">Founder AI Assistant</h3>
                <p className="text-xs text-slate-500 max-w-sm leading-relaxed">
                  I search across your uploaded PDF knowledge base to answer questions and reference sources.
                </p>
              </div>

              <div className="space-y-3">
                <p className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Suggested Questions</p>
                <div className="grid grid-cols-1 gap-2.5 max-w-lg mx-auto">
                  {starterPrompts.map((prompt, i) => (
                    <button
                      key={i}
                      onClick={() => handleSendMessage(undefined, prompt)}
                      className="text-left px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 hover:bg-indigo-500/5 hover:border-indigo-500/30 text-xs text-slate-700 font-medium transition-all cursor-pointer"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-4">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] rounded-2xl p-4 text-sm leading-relaxed ${
                      msg.role === 'user'
                        ? 'chat-bubble-user text-white'
                        : 'chat-bubble-agent text-slate-800'
                    }`}
                  >
                    {/* Live tool-activity chips (agentic pipeline progress) */}
                    {msg.role === 'assistant' && msg.activities && msg.activities.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mb-2.5">
                        {msg.activities.map((act, idx) => (
                          <span
                            key={idx}
                            className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-lg text-[10px] font-semibold border ${
                              act.status === 'running'
                                ? 'bg-indigo-50 border-indigo-200 text-indigo-700'
                                : 'bg-emerald-50 border-emerald-200 text-emerald-700'
                            }`}
                          >
                            {act.status === 'running' ? (
                              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
                            ) : (
                              <span>✓</span>
                            )}
                            {act.label}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Streaming text with typing cursor, or "thinking" dots before first token */}
                    {msg.role === 'assistant' && msg.isStreaming && !msg.content ? (
                      <div className="flex items-center gap-2 py-1">
                        <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    ) : (
                      <p className="whitespace-pre-line">
                        {msg.content}
                        {msg.isStreaming && <span className="inline-block w-1.5 h-3.5 ml-0.5 bg-indigo-400 align-middle animate-pulse" />}
                      </p>
                    )}

                    {/* Escalation ticket notice */}
                    {msg.role === 'assistant' && msg.ticket && (
                      <div className="mt-3 pt-2.5 border-t border-slate-200 flex items-center gap-2 text-[11px] text-amber-700">
                        <span>🎫</span>
                        <span>
                          Support ticket <span className="font-mono">#{msg.ticket.id.slice(0, 8)}</span> created — &quot;{msg.ticket.subject}&quot;
                        </span>
                      </div>
                    )}

                    {/* Citations Toggle */}
                    {msg.role === 'assistant' && msg.sources && msg.sources.length > 0 && (
                      <div className="mt-3 pt-2.5 border-t border-slate-200 flex items-center gap-2">
                        <span className="text-[10px] text-slate-500 font-bold">SOURCES:</span>
                        <div className="flex flex-wrap gap-1.5">
                          {msg.sources.map((cite, idx) => (
                            <button
                              key={idx}
                              onClick={() => msg.sources && handleCitationClick(msg.sources, msg.content)}
                              className="px-2 py-0.5 rounded bg-slate-100 hover:bg-indigo-100 hover:text-indigo-700 text-[10px] text-slate-500 font-semibold transition-colors cursor-pointer border border-slate-200"
                            >
                              {cite.type === 'web' ? '🌐' : '📄'} {cite.document}
                              {cite.type !== 'web' && cite.page ? ` (p. ${cite.page})` : ''}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl text-center max-w-md mx-auto">
                  {error}
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-slate-200 bg-white">
          <form onSubmit={handleSendMessage} className="max-w-3xl mx-auto flex gap-2.5">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
              placeholder="Ask support agent based on documents..."
              className="flex-1 px-4 py-3.5 rounded-xl glass-input text-sm placeholder:text-slate-500 text-slate-900 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="px-5 bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-600 hover:to-violet-700 disabled:from-slate-200 disabled:to-slate-200 disabled:text-slate-500 text-white rounded-xl text-sm font-semibold shadow-lg shadow-indigo-500/20 active:scale-[0.98] transition-all flex items-center justify-center cursor-pointer disabled:scale-100 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </form>
        </div>
      </div>

      {/* Citations Sliding Side Panel */}
      {activeCitations && (
        <div className="w-80 border-l border-slate-200 bg-white p-6 overflow-y-auto shrink-0 flex flex-col animate-fade-in relative z-10">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-sm font-bold text-slate-900">Source Citations</h3>
            <button
              onClick={() => setActiveCitations(null)}
              className="text-slate-500 hover:text-slate-900 p-1 hover:bg-slate-100 rounded-lg text-xs cursor-pointer"
            >
              ✕ Close
            </button>
          </div>
          
          <div className="mb-4">
            <p className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Answer Context</p>
            <p className="text-xs text-slate-500 mt-1 italic leading-relaxed">"{citationsFileName}"</p>
          </div>

          <div className="space-y-3.5 flex-1 overflow-y-auto">
            <p className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Referenced Sources</p>
            {activeCitations.map((cite, i) => (
              <div key={i} className="glass-card p-4 rounded-xl space-y-2">
                <div className="flex items-start gap-2.5">
                  <span className="text-lg">{cite.type === 'web' ? '🌐' : '📄'}</span>
                  <div className="min-w-0">
                    <p className="text-xs font-bold text-slate-800 truncate" title={cite.document}>
                      {cite.document}
                    </p>
                    {cite.type === 'web' ? (
                      cite.url ? (
                        <a
                          href={cite.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[10px] text-indigo-600 font-semibold mt-0.5 truncate block hover:underline"
                        >
                          {cite.url}
                        </a>
                      ) : (
                        <p className="text-[10px] text-indigo-600 font-semibold mt-0.5">Web result</p>
                      )
                    ) : (
                      <p className="text-[10px] text-indigo-600 font-semibold mt-0.5">
                        Page Number: {cite.page}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
