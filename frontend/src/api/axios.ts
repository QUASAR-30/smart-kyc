import axios from 'axios';

// On utilise le chemin relatif '/api' pour passer par le proxy Vite
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// 1. Intercepteur de REQUÊTE : Ajoute le Token automatiquement
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 2. Intercepteur de RÉPONSE : Gère l'expiration du Token
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Si on reçoit une erreur 401 (Non autorisé), c'est que le token est mort
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('access_token');
      // Redirection brute vers login si nécessaire
      window.location.href = '/'; 
    }
    return Promise.reject(error);
  }
);

export default api;
