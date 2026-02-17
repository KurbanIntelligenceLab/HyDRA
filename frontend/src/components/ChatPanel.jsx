import { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Bot, User, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { sendChat } from '../api';

const QUICK_QUESTIONS = [
  "Why does Zr decoration improve H2 deliverability?",
  "What's the correlation between band gap and adsorption energy?",
  "Suggest next dopants to test based on this data",
  "Compare electronic properties across all systems",
  "What's the optimal decoration level for reversible storage?",
  "Find an interpretable formula for Eads",
];

export default function ChatPanel({ project, onAgentActivity, messages: externalMessages, setMessages: externalSetMessages }) {
  // Use external state if provided, otherwise use internal state (backwards compatibility)
  const [internalMessages, setInternalMessages] = useState([]);
  const messages = externalMessages !== undefined ? externalMessages : internalMessages;
  const setMessages = externalSetMessages !== undefined ? externalSetMessages : setInternalMessages;

  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeAgents, setActiveAgents] = useState([]);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (quickQuery = null) => {
    const query = quickQuery ? quickQuery.trim() : input.trim();
    if (!query || loading) return;
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: query }]);
    setLoading(true);
    setActiveAgents([]);

    try {
      const result = await sendChat(query, project);
      setActiveAgents(result.active_agents || []);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: result.response,
          agents: result.active_agents,
          agentResults: result.agent_results,
        },
      ]);
      onAgentActivity?.({
        query,
        agents: result.active_agents,
        agentResults: result.agent_results,
      });
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Error: ${err.message}` },
      ]);
    } finally {
      setLoading(false);
      setActiveAgents([]);
    }
  };

  const AGENT_COLORS = {
    descriptor: 'bg-purple-100 text-purple-700',
    structure: 'bg-green-100 text-green-700',
    thermo: 'bg-orange-100 text-orange-700',
    screening: 'bg-blue-100 text-blue-700',
    reasoning: 'bg-rose-100 text-rose-700',
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200">
      {/* Quick questions */}
      <div className="p-4 border-b border-slate-100 bg-slate-50 rounded-t-xl">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="w-4 h-4 text-blue-600" />
          <span className="text-sm font-medium text-slate-700">Quick questions</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {QUICK_QUESTIONS.map((q, i) => (
            <button
              key={i}
              onClick={() => handleSend(q)}
              disabled={loading}
              className="text-xs bg-white hover:bg-blue-50 text-slate-600 px-3 py-1.5 rounded-full border border-slate-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Messages */}
      <div className="h-[250px] overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-16 text-slate-400">
            <Bot className="w-12 h-12 mx-auto mb-3" />
            <p className="font-medium">Ask me anything about your materials data</p>
            <p className="text-sm mt-1">I'll route your query to the right specialist agent(s)</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[75%] ${msg.role === 'user' ? '' : ''}`}>
              {/* Agent badges */}
              {msg.agents && msg.agents.length > 0 && (
                <div className="flex gap-1 mb-1">
                  {msg.agents.map((a) => (
                    <span key={a} className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${AGENT_COLORS[a] || 'bg-slate-100 text-slate-600'}`}>
                      {a}
                    </span>
                  ))}
                </div>
              )}
              <div
                className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white rounded-br-md'
                    : 'bg-slate-100 text-slate-800 rounded-bl-md'
                }`}
              >
                {msg.role === 'assistant' ? (
                  <ReactMarkdown className="prose prose-sm max-w-none prose-slate">
                    {msg.content}
                  </ReactMarkdown>
                ) : (
                  msg.content
                )}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-slate-400 text-sm">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>
              {activeAgents.length > 0
                ? `Agents working: ${activeAgents.join(', ')}...`
                : 'Routing query...'}
            </span>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-slate-100 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
          placeholder="Ask about correlations, predict dopants, compute thermodynamics..."
          className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white px-4 py-2.5 rounded-xl transition-colors"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
