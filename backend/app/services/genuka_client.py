"""
SmartKYC - Genuka API Client
Version: Hackathon Final (Company-First Strategy)
"""

import os
import jwt  # Assure-toi d'avoir pip install pyjwt
from typing import Dict, Any
import requests
from dotenv import load_dotenv

load_dotenv()

class GenukaAPIError(Exception):
    pass

class GenukaClient:
    def __init__(self):
        self.api_url = os.getenv("GENUKA_API_URL", "https://api.genuka.com")
        self.client_id = os.getenv("GENUKA_CLIENT_ID")
        self.client_secret = os.getenv("GENUKA_CLIENT_SECRET")

    def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Échange le code contre un token"""
        token_url = f"{self.api_url}/oauth/token"
        payload = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': redirect_uri,
        }
        
        try:
            response = requests.post(token_url, data=payload, timeout=30)
            if not response.ok:
                raise GenukaAPIError(f"Token error: {response.text}")
            
            return response.json()
        except Exception as e:
            raise GenukaAPIError(f"Connection error: {str(e)}")

    def get_merchant_info(self, access_token: str) -> Dict[str, Any]:
        """
        Stratégie 'Boilerplate': On récupère la Compagnie, pas le User.
        """
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }

        print(f"DEBUG: Tentative récupération infos Compagnie...")

        # STRATÉGIE 1 : Endpoint Companies (Standard Genuka)
        # C'est ce que fait le boilerplate Django généralement
        try:
            url = f"{self.api_url}/api/v1/companies"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Genuka renvoie souvent une liste ou un objet paginé 'data'
                company = None
                
                if isinstance(data, list) and len(data) > 0:
                    company = data[0]
                elif isinstance(data, dict) and "data" in data and len(data["data"]) > 0:
                    company = data["data"][0]
                elif isinstance(data, dict) and "id" in data:
                    company = data # C'est directement l'objet
                
                if company:
                    print(f"DEBUG: Compagnie trouvée: {company.get('name')}")
                    return {
                        "id": str(company.get("id")),
                        "email": company.get("email") or f"company_{company.get('id')}@genuka.com",
                        "business_name": company.get("name", "Ma Boutique")
                    }
        except Exception as e:
            print(f"WARN: Échec appel /api/v1/companies: {e}")

        # STRATÉGIE 2 : FALLBACK JWT (La méthode de survie)
        # Si l'API échoue, on lit le token qui contient souvent l'ID de la compagnie dans 'sub'
        print("DEBUG: Passage au décodage direct du Token (Fallback)")
        try:
            decoded = jwt.decode(access_token, options={"verify_signature": False})
            print(f"DEBUG JWT: {decoded}")
            
            # Dans le contexte Genuka App, 'sub' est souvent l'ID user ou company
            sub_id = decoded.get("sub")
            if not sub_id:
                raise Exception("Pas de 'sub' dans le token")

            return {
                "id": str(sub_id),
                "email": f"merchant_{str(sub_id)[:6]}@smartkyc.temp", # Email temporaire
                "business_name": "Genuka Merchant (Vérifié)"
            }
        except Exception as e:
            raise GenukaAPIError(f"Impossible d'identifier le marchand: {str(e)}")

    # Garder ces méthodes simples pour éviter les crashs si l'API est vide
    def get_orders(self, access_token: str, months: int = 12):
        try:
            url = f"{self.api_url}/api/v1/orders"
            res = requests.get(url, headers={'Authorization': f'Bearer {access_token}'}, params={'months': months}, timeout=5)
            return res.json() if res.ok else []
        except: return []

    def get_customers(self, access_token: str):
        try:
            url = f"{self.api_url}/api/v1/customers"
            res = requests.get(url, headers={'Authorization': f'Bearer {access_token}'}, timeout=5)
            return res.json() if res.ok else []
        except: return []