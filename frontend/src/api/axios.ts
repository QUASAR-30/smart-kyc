import axios from 'axios';

// On utilise le chemin relatif '/api' pour passer par le proxy Vite
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

import { fetchParameterByUrl } from '../utils/url';

api.interceptors.request.use((config) => {

  if (typeof window !== "undefined") {
    const urlParams = new URLSearchParams(window.location.search);



    const { hmac, timestamp, companyId } = fetchParameterByUrl(window.location.href);


    if (hmac || timestamp || companyId) {
      config.params = {
        ...(config.params || {}),
        ...(hmac && { hmac }),
        ...(timestamp && { timestamp }),
        ...(companyId && { company_id: companyId }),
      };
    }
  }

  return config;
});

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
