'use client';

import { useState, useRef, useEffect } from 'react';
import styles from './ChatAssistant.module.css';
import { MessageSquareCode, Send, Bot, User, Loader2, Info, FileText, AlertTriangle } from 'lucide-react';
import { askAssistant, getHealth } from '@/lib/api';

const WELCOME_MSG = {
  role: 'assistant',
  content:
    "Hello! I'm the **FloodGuard AI Assistant**. I answer from a vector index built over official " +
    "NDMA, IMD and NDRF publications, and I cite the document and page behind every answer.\n\n" +
    "Ask me about flood safety and evacuation procedures, how to read IMD colour warnings, " +
    "urban flooding and flood-plain zoning guidance, or community disaster preparedness.",
  ts: new Date(),
};


/**
 * Turn an axios failure into something a person can act on.
 *
 * Two traps this avoids. FastAPI returns validation errors as an ARRAY of objects,
 * so interpolating `detail` straight into a template literal renders
 * "[object Object]". And a response with an error status means the API answered —
 * reporting that as "could not reach the API" sends the reader after the wrong
 * problem entirely.
 */
function describeError(err) {
  const response = err?.response;

  // No response at all: genuinely unreachable.
  if (!response) {
    return 'Could not reach the FloodGuard API. The ingestion service may not be running.';
  }

  const detail = response.data?.detail;
  let message;

  if (Array.isArray(detail)) {
    // Pydantic validation errors: [{ loc, msg, type }, …]
    message = detail
      .map(d => (typeof d === 'string' ? d : d?.msg))
      .filter(Boolean)
      .join('; ');
  } else if (typeof detail === 'string') {
    message = detail;
  } else if (detail) {
    message = JSON.stringify(detail);
  }

  if (response.status === 422) {
    return `That question could not be processed: ${message || 'invalid input'}.`;
  }
  if (response.status === 503) {
    return message || 'The assistant is unavailable — the knowledge base may not be built yet.';
  }
  return `The assistant returned an error (${response.status})${message ? `: ${message}` : '.'}`;
}

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
    getHealth().then(setHealth).catch(() => setHealth({ unreachable: true }));
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
        // A configured key that is failing must look different from no key at all.
        llmError: res.llm_error_reason && res.llm_error_reason !== 'no_key'
          ? res.llm_error : null,
        ts: new Date(),
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        error: true,
        content: describeError(err),
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
    if (health.unreachable) return 'FloodGuard API unreachable — start the FastAPI service on port 8000.';
    const chunks = health.rag?.chunks ?? 0;
    const llm = health.llm?.configured
      ? `${health.llm.model} generating answers`
      : 'no Gemini key — returning source passages verbatim. Add GEMINI_API_KEY to apps/api/.env for written answers.';
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

                {m.llmError && (
                  <div className={styles.llmError}>
                    <AlertTriangle size={13} />
                    <span>Gemini failed, so the sources are shown unsummarised — {m.llmError}</span>
                  </div>
                )}

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
