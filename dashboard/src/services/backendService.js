import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const backendService = {
    // Events
    getEvents: async (params = {}) => {
        const { data } = await apiClient.get('/events', { params });
        return data.data;
    },
    getActiveEvents: async () => {
        const { data } = await apiClient.get('/events/active');
        return data.data;
    },
    getEvent: async (eventId) => {
        const { data } = await apiClient.get(`/events/${eventId}`);
        return data.data;
    },

    // Stations / Rivers
    getStations: async () => {
        const { data } = await apiClient.get('/stations');
        return data.data;
    },
    getRivers: async () => {
        const { data } = await apiClient.get('/rivers');
        return data.data;
    },

    // Weather
    getWeather: async (params = {}) => {
        const { data } = await apiClient.get('/weather', { params });
        return data.data;
    },

    // Predictions
    getPredictions: async (params = {}) => {
        const { data } = await apiClient.get('/predictions', { params });
        return data.data;
    },

    // Chat
    chat: async (question) => {
        const { data } = await apiClient.post('/chat', { question });
        return data;
    },
};

export default backendService;
