/**
 * api.js — the single client for the FloodGuard gateway.
 *
 * Everything goes through same-origin `/api/*`, which next.config.mjs rewrites to the
 * FastAPI service. The browser never learns the backend hostname, there is no CORS
 * negotiation, and the web app has exactly one upstream — it does not talk to IMD.
 */
import axios from 'axios';

const client = axios.create({
  baseURL: '/api',
  timeout: 60_000,                       // /chat waits on Gemini
  headers: { 'Content-Type': 'application/json' },
});

/** Subsystem status: DB counts, ML model, RAG index, LLM key. */
export const getHealth = () => client.get('/health').then(r => r.data);

/** Location registry, served by the backend so districts are defined in one place. */
export const getDistricts = () => client.get('/districts').then(r => r.data);

/** Everything one district view needs, in a single round trip. */
export const getDashboard = (district) =>
  client.get(`/dashboard/${encodeURIComponent(district)}`).then(r => r.data);

/** Correlated flood events across all districts. */
export const getEvents = (params = {}) => client.get('/events', { params }).then(r => r.data);

/** One event plus its full evidence trail. */
export const getEvent = (id) => client.get(`/events/${id}`).then(r => r.data);

/** Stored ML scoring history. */
export const getPredictions = (params = {}) =>
  client.get('/predictions', { params }).then(r => r.data);

/** Grounded RAG answer with citations. */
export const askAssistant = (question, topK) =>
  client.post('/chat', { question, top_k: topK }).then(r => r.data);

/** Force a collection cycle instead of waiting for the scheduler. */
export const runIngest = () => client.post('/ingest/run').then(r => r.data);

/** Free-text place search. Returns candidates that are not yet followed. */
export const searchPlaces = (q, country = 'IN') =>
  client.get('/districts/search', { params: { q, country } }).then(r => r.data);

/** Start following a place — the next collection cycle picks it up. */
export const trackPlace = ({ district, state, latitude, longitude, country = 'IN' }) =>
  client.post('/districts/track', null, {
    params: { district, state, latitude, longitude, country },
  }).then(r => r.data);

/** Stop following a place. */
export const untrackPlace = (district) =>
  client.delete(`/districts/track/${encodeURIComponent(district)}`).then(r => r.data);

/** Name the place at a coordinate — backs "use my location". */
export const reverseLookup = (lat, lon) =>
  client.get('/districts/reverse', { params: { lat, lon } }).then(r => r.data);

export default client;
