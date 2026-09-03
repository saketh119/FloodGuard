import { useState, useRef, useEffect } from 'react';
import styles from './ChatAssistant.module.css';
import { MessageSquareCode, Send, Bot, User, Loader2, Info, FileText, AlertTriangle } from 'lucide-react';
import { askAssistant, fetchHealth, API_BASE } from '../../services/floodguardService';

const WELCOME_MSG = {
  role: 'assistant',
  content:
    "Hello! I'm the **FloodGuard AI Assistant**. I answer from a vector index built over official " +
    "NDMA, IMD and NDRF publications, and I cite the document and page behind every answer.\n\n" +
    "Ask me about flood safety and evacuation procedures, how to read IMD colour warnings, " +
    "urban flooding and flood-plain zoning guidance, or community disaster preparedness.",
  ts: new Date(),
};

export default function ChatAssistant() {
  const [messages, setMessages] = useState([WELCOME_MSG]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [health, setHealth] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Tell the user up front which half of the stack is live, rather than
  // silently degrading when the index or the LLM key is missing.
  useEffect(() => {
    fetchHealth().then(setHealth).catch(() => setHealth({ unreachable: true }));
  }, []);

  const sendMessage = async (preset) => {
    const q = (preset ?? input).trim();
    if (!q || sending) return;
    setInput('');
    setSending(true);
    setMessages(prev => [...prev, { role: 'user', content: q, ts: new Date() }]);

    try {
      const res = await askAssistant(q);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: res.answer,
        citations: res.citations ?? [],
        llmUsed: res.llm_used,
        ts: new Date(),
      }]);
    } catch (err) {
      const detail = err?.response?.data?.detail ?? err?.message ?? 'Unknown error';
      setMessages(prev => [...prev, {
        role: 'assistant',
        error: true,
        content: `Could not reach the FloodGuard backend at \`${API_BASE}\`.\n\n${detail}\n\nStart it with: \`uvicorn app.main:app --port 8000\` from the \`backend/\` directory.`,
        ts: new Date(),
      }]);
    } finally {
      setSending(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  const renderStatus = () => {
    if (!health) return 'Checking backend…';
    if (health.unreachable) return `Backend unreachable at ${API_BASE} — start the FastAPI service.`;
    const chunks = health.rag?.chunks ?? 0;
    const llm = health.llm?.configured
      ? `${health.llm.model} generating answers`
      : 'no Gemini key — returning source passages verbatim instead of generated answers';
    return `${chunks.toLocaleString()} indexed passages · ${llm}`;
  };

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.title}><MessageSquareCode size={22} /> Chat Assistant</h1>
        <p className={styles.subtitle}>Retrieval-augmented Q&A grounded in NDMA, IMD and NDRF publications</p>
      </div>

      <div className={styles.ragStatus}>
        {health?.unreachable ? <AlertTriangle size={14} /> : <Info size={14} />}
        <span>{renderStatus()}</span>
      </div>

      <div className={styles.chatWindow}>
        <div className={styles.messages}>
          {messages.map((m, i) => (
            <div key={i} className={`${styles.msg} ${m.role === 'user' ? styles.user : styles.bot}`}>
              <div className={styles.avatar}>
                {m.role === 'user' ? <User size={16} /> : <Bot size={16} />}
              </div>
              <div className={styles.bubble}>
                <div className={styles.bubbleContent}>
                  {m.content.split('\n').map((line, j) => (
                    <p key={j} style={{ margin: '2px 0' }}
                      dangerouslySetInnerHTML={{
                        __html: line
                          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                          .replace(/`(.*?)`/g, '<code>$1</code>'),
                      }}
                    />
                  ))}
                </div>

                {m.citations?.length > 0 && (
                  <div className={styles.citations}>
                    <span className={styles.citationsLabel}><FileText size={12} /> Sources</span>
                    {m.citations.map((c, k) => (
                      <span key={k} className={styles.citation} title={c.source_org ?? ''}>
                        {c.title}{c.page ? `, p.${c.page}` : ''}
                        {c.relevance != null && <em> · {(c.relevance * 100).toFixed(0)}%</em>}
                      </span>
                    ))}
                  </div>
                )}

                <div className={styles.ts}>
                  {m.ts.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
                  {m.llmUsed === false && ' · unsummarised source text'}
                </div>
              </div>
            </div>
          ))}
          {sending && (
            <div className={`${styles.msg} ${styles.bot}`}>
              <div className={styles.avatar}><Bot size={16} /></div>
              <div className={styles.bubble}>
                <div className={styles.typing}>
                  <Loader2 size={14} className={styles.spin} />
                  <span>Searching the guidelines…</span>
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className={styles.inputRow}>
          <textarea
            className={styles.input}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask about flood safety, IMD warnings, evacuation procedures…"
            rows={2}
          />
          <button className={styles.sendBtn} onClick={() => sendMessage()} disabled={!input.trim() || sending}>
            {sending ? <Loader2 size={18} className={styles.spin} /> : <Send size={18} />}
          </button>
        </div>
      </div>

      <div className={styles.suggestions}>
        <span className={styles.sugLabel}>Try asking:</span>
        {[
          'What does an Orange IMD warning mean?',
          'What are the NDMA flood evacuation procedures?',
          'How should urban flooding be managed in cities?',
        ].map(q => (
          <button key={q} className={styles.sugBtn} onClick={() => sendMessage(q)} disabled={sending}>
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
