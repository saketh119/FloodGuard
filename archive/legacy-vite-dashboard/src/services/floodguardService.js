/**
 * floodguardService.js
 *
 * Client for the FloodGuard backend (FastAPI, default :8000).
 *
 * This is a different upstream from imdService.js on purpose. imdService talks to the
 * raw IMD feed; this talks to the platform that has already ingested that feed,
 * detected triggers, correlated them into events, scored them and summarised them.
 */

import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 60_000,           // /chat waits on Gemini
  headers: { 'Content-Type': 'application/json' },
});

/** Which subsystems are actually up — model loaded, RAG indexed, LLM keyed. */
export async function fetchHealth() {
  const { data } = await client.get('/health');
  return data;
}

/** Correlated flood events, highest risk first. */
export async function fetchEvents(params = {}) {
  const { data } = await client.get('/events', { params });
  return data;
}

/** One event plus the full evidence trail behind it. */
export async function fetchEvent(eventId) {
  const { data } = await client.get(`/events/${eventId}`);
  return data;
}

/** Stored ML scoring history, for trend charts. */
export async function fetchPredictions(params = {}) {
  const { data } = await client.get('/predictions', { params });
  return data;
}

/** Ask the RAG assistant. Returns { answer, citations, grounded, llm_used }. */
export async function askAssistant(question, topK) {
  const { data } = await client.post('/chat', { question, top_k: topK });
  return data;
}

/** Force a pipeline pass instead of waiting for the scheduler. */
export async function runIngest() {
  const { data } = await client.post('/ingest/run');
  return data;
}

export { API_BASE };
