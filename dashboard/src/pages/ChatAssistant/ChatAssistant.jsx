import { useState, useRef, useEffect } from 'react';
import styles from './ChatAssistant.module.css';
import { MessageSquareCode, Send, Bot, User, Loader2, Info } from 'lucide-react';

const RAG_BASE = import.meta.env.VITE_RAG_BASE_URL || 'http://localhost:8000';

const WELCOME_MSG = {
  role: 'assistant',
  content: `Hello! I'm the **FloodGuard AI Assistant**, powered by the RAG (Retrieval-Augmented Generation) knowledge base built from NDMA, IMD, and NDRF documents.\n\nI can answer questions about:\n- Flood safety and evacuation procedures\n- IMD weather warnings interpretation\n- NDRF response guidelines\n- River basin flood patterns\n\nThe RAG backend is currently running as a CLI. Once we expose it as a FastAPI endpoint at \`${RAG_BASE}\`, I'll connect automatically. For now, try asking me anything — sample answers are prepared.`,
  ts: new Date(),
};

const SAMPLE_ANSWERS = {
  flood: 'According to the NDMA Flood Management guidelines, during a flood warning: 1) Move to higher ground immediately, 2) Avoid walking in moving water, 3) Do not drive through floodwaters, 4) Listen to emergency broadcasts on All India Radio.',
  warning: 'IMD uses a 4-color warning system — Green (No action), Yellow (Watch), Orange (Alert/Be prepared), Red (Warning/Take action). Red warnings indicate extreme weather requiring immediate protective action.',
  ndrf: 'The NDRF (National Disaster Response Force) is the specialized force for disaster response. For flood rescue, contact: 011-24363260 or visit ndrf.gov.in. NDRF teams can be deployed within 4-6 hours of a warning.',
  evacuate: 'IMD standard evacuation protocol: 1) District Collector issues evacuation notice, 2) NDRF teams pre-positioned, 3) Evacuate 24h before predicted peak flood, 4) Use designated shelter routes only, 5) Carry emergency kit (documents, medicine, water, food for 3 days).',
  default: 'I\'m connecting to the FloodGuard RAG knowledge base which has indexed NDMA, IMD, and NDRF flood management documents. The backend is exposed once you run `python rag/app.py` as a server. Your question has been noted!',
};

function getSampleAnswer(q) {
  q = q.toLowerCase();
  if (q.includes('flood') || q.includes('water')) return SAMPLE_ANSWERS.flood;
  if (q.includes('warning') || q.includes('color') || q.includes('colour') || q.includes('alert')) return SAMPLE_ANSWERS.warning;
  if (q.includes('ndrf') || q.includes('rescue') || q.includes('force')) return SAMPLE_ANSWERS.ndrf;
  if (q.includes('evacuat') || q.includes('escape') || q.includes('leave')) return SAMPLE_ANSWERS.evacuate;
  return SAMPLE_ANSWERS.default;
}

async function queryRag(question) {
  try {
    const res = await fetch(`${RAG_BASE}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });
    if (!res.ok) throw new Error('RAG unavailable');
    const data = await res.json();
    return data.answer ?? data.response ?? 'No answer returned.';
  } catch {
    // Fall back to sample answer
    return getSampleAnswer(question);
  }
}

export default function ChatAssistant() {
  const [messages, setMessages] = useState([WELCOME_MSG]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    const q = input.trim();
    if (!q || sending) return;
    setInput('');
    setSending(true);
    setMessages(prev => [...prev, { role: 'user', content: q, ts: new Date() }]);
    const answer = await queryRag(q);
    setMessages(prev => [...prev, { role: 'assistant', content: answer, ts: new Date() }]);
    setSending(false);
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.title}><MessageSquareCode size={22} /> Chat Assistant</h1>
        <p className={styles.subtitle}>RAG-powered flood intelligence Q&A · Indexed from NDMA, IMD, and NDRF documents</p>
      </div>

      <div className={styles.ragStatus}>
        <Info size={14} />
        <span>RAG backend: <code>{RAG_BASE}/query</code> — trying to connect. Falls back to sample answers if unreachable.</span>
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
                      dangerouslySetInnerHTML={{ __html: line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/`(.*?)`/g, '<code>$1</code>') }}
                    />
                  ))}
                </div>
                <div className={styles.ts}>{m.ts.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}</div>
              </div>
            </div>
          ))}
          {sending && (
            <div className={`${styles.msg} ${styles.bot}`}>
              <div className={styles.avatar}><Bot size={16} /></div>
              <div className={styles.bubble}>
                <div className={styles.typing}>
                  <Loader2 size={14} className={styles.spin} />
                  <span>Searching knowledge base…</span>
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
          <button className={styles.sendBtn} onClick={sendMessage} disabled={!input.trim() || sending}>
            {sending ? <Loader2 size={18} className={styles.spin} /> : <Send size={18} />}
          </button>
        </div>
      </div>

      <div className={styles.suggestions}>
        <span className={styles.sugLabel}>Try asking:</span>
        {['What does an Orange IMD warning mean?', 'How to evacuate during a flood?', 'What is NDRF response time?'].map(q => (
          <button key={q} className={styles.sugBtn} onClick={() => { setInput(q); }}>
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
