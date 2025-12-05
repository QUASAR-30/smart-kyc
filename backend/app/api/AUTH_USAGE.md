# SmartKYC - Authentication Module Guide

## Vue d'ensemble

Le module d'authentification fournit une authentification JWT simple pour le hackathon, avec auto-signup (création automatique du compte marchand).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend                                                    │
│  POST /auth/mock-login { "email": "user@example.cm" }      │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend API (auth.py)                                       │
│  1. Check if merchant exists in DB                          │
│  2. If not exists → Auto-create (auto-signup)              │
│  3. Generate JWT token                                      │
│  4. Return token + merchant info                            │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Protected Routes                                            │
│  Authorization: Bearer <token>                              │
│  → get_current_merchant() validates token                  │
│  → Returns Merchant object                                  │
└─────────────────────────────────────────────────────────────┘
```

## Fichiers Créés

### 1. Utils JWT ([backend/app/utils/jwt_handler.py](../utils/jwt_handler.py))

```python
create_access_token(data, expires_delta)  # Créer token JWT
verify_token(token)                        # Vérifier et décoder token
get_token_expiry(token)                    # Obtenir expiration
decode_token(token)                        # Décoder sans vérifier (debug)
```

### 2. Schemas Pydantic

#### [backend/app/schemas/token.py](../schemas/token.py)
```python
Token           # Response avec access_token
TokenData       # Payload du JWT (merchant_id, email)
```

#### [backend/app/schemas/merchant.py](../schemas/merchant.py)
```python
MerchantCreate          # Création marchand
MerchantUpdate          # Mise à jour marchand
MerchantResponse        # Response marchand
MerchantLoginRequest    # Request login (email seulement)
MerchantLoginResponse   # Response login (token + merchant)
```

### 3. API Endpoints ([backend/app/api/auth.py](auth.py))

```python
POST /auth/mock-login    # Login avec auto-signup
GET /auth/me             # Informations marchand authentifié
get_current_merchant()   # Dependency pour routes protégées
```

## Utilisation

### 1. Mock Login (Auto-Signup)

**Endpoint** : `POST /auth/mock-login`

**Request** :
```json
{
  "email": "kouassi@example.cm"
}
```

**Response** (200 OK) :
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "merchant": {
    "id": "a1b2c3d4-...",
    "email": "kouassi@example.cm",
    "business_name": "Business - Kouassi",
    "genuka_merchant_id": null,
    "subscription_tier": "FREE",
    "created_at": "2025-12-05T00:00:00",
    "updated_at": "2025-12-05T00:00:00"
  }
}
```

**Comportement** :
- ✅ Si marchand n'existe pas → le crée automatiquement (auto-signup)
- ✅ Si marchand existe déjà → retourne nouveau token
- ✅ Pas de password requis (hackathon simplification)
- ✅ Token expire après 60 minutes (configurable dans .env)

**cURL Example** :
```bash
curl -X POST http://localhost:8000/auth/mock-login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.cm"}'
```

**Python Example** :
```python
import requests

response = requests.post(
    "http://localhost:8000/auth/mock-login",
    json={"email": "kouassi@example.cm"}
)

data = response.json()
access_token = data["access_token"]
merchant_id = data["merchant"]["id"]
```

### 2. Get Current Merchant

**Endpoint** : `GET /auth/me`

**Headers** :
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK) :
```json
{
  "id": "a1b2c3d4-...",
  "email": "kouassi@example.cm",
  "business_name": "Business - Kouassi",
  "genuka_merchant_id": null,
  "subscription_tier": "FREE",
  "created_at": "2025-12-05T00:00:00",
  "updated_at": "2025-12-05T00:00:00"
}
```

**Errors** :
- **401 Unauthorized** : Token invalide, expiré, ou manquant
- **401 Unauthorized** : Marchand introuvable

**cURL Example** :
```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer <votre_token>"
```

**Python Example** :
```python
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(
    "http://localhost:8000/auth/me",
    headers=headers
)

merchant = response.json()
print(f"Logged in as: {merchant['email']}")
```

### 3. Routes Protégées

Utilisez la dépendance `get_current_merchant` pour protéger vos routes :

```python
from fastapi import APIRouter, Depends
from app.api.auth import get_current_merchant
from app.models import Merchant

router = APIRouter()

@router.get("/trustscores/latest")
def get_latest_trustscore(
    merchant: Merchant = Depends(get_current_merchant)
):
    """
    Route protégée - requiert authentification.
    """
    # merchant est automatiquement récupéré depuis le token
    return {
        "merchant_id": merchant.id,
        "email": merchant.email,
        "trustscore": 750  # Example
    }
```

**Exemple d'utilisation** :
```bash
# Sans token → 401 Unauthorized
curl http://localhost:8000/trustscores/latest

# Avec token → 200 OK
curl http://localhost:8000/trustscores/latest \
  -H "Authorization: Bearer <token>"
```

## Configuration (.env)

```bash
# JWT Configuration
SECRET_KEY=your-super-secret-key-change-me-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60  # 1 heure

# Database
DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/smartkyc_db
```

## Fonctionnement Interne

### 1. Création du Token JWT

```python
from app.utils import create_access_token

# Créer token
token = create_access_token(
    data={"sub": merchant.id, "email": merchant.email}
)

# Token contient :
# {
#   "sub": "merchant-id",     # Subject (merchant ID)
#   "email": "user@example.cm",
#   "exp": 1733450000         # Expiration timestamp
# }
```

### 2. Vérification du Token

```python
from app.utils import verify_token

# Vérifier token
payload = verify_token(token)

if payload:
    merchant_id = payload.get("sub")
    email = payload.get("email")
else:
    # Token invalide ou expiré
    raise HTTPException(status_code=401)
```

### 3. Auto-Signup Flow

```python
# Dans mock_login()
merchant = db.query(Merchant).filter(
    Merchant.email == request.email
).first()

if not merchant:
    # Auto-create merchant
    merchant = Merchant(
        id=str(uuid.uuid4()),
        email=request.email,
        business_name=f"Business - {email_prefix}",
        subscription_tier=SubscriptionTier.FREE
    )
    db.add(merchant)
    db.commit()
```

### 4. Dépendance get_current_merchant

```python
def get_current_merchant(
    authorization: str = Header(),
    db: Session = Depends(get_db)
) -> Merchant:
    # 1. Extract token from "Bearer <token>"
    scheme, token = authorization.split()

    # 2. Verify token
    payload = verify_token(token)

    # 3. Get merchant_id from payload
    merchant_id = payload.get("sub")

    # 4. Fetch merchant from database
    merchant = db.query(Merchant).filter(
        Merchant.id == merchant_id
    ).first()

    # 5. Return merchant or raise 401
    return merchant
```

## Frontend Integration

### React/TypeScript Example

```typescript
// Login
async function login(email: string) {
  const response = await fetch('http://localhost:8000/auth/mock-login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email })
  });

  const data = await response.json();

  // Store token in localStorage
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('merchant', JSON.stringify(data.merchant));

  return data;
}

// Call protected endpoint
async function getLatestTrustScore() {
  const token = localStorage.getItem('access_token');

  const response = await fetch('http://localhost:8000/trustscores/latest', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (response.status === 401) {
    // Token expired or invalid → redirect to login
    window.location.href = '/login';
    return;
  }

  return await response.json();
}

// Axios interceptor
import axios from 'axios';

axios.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Token expired → logout
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

## Tests

### Exécuter les tests :

```bash
cd /home/quasars/Documents/smartkyc-hackathon/smartkyc/backend
python3 test_auth.py
```

### Tests inclus :
1. ✅ JWT token creation and verification
2. ✅ Token expiration handling
3. ✅ Invalid token rejection
4. ✅ Database merchant creation
5. ✅ Mock login with auto-signup
6. ✅ Get current merchant dependency

## Swagger UI (FastAPI Docs)

Démarrer le serveur :
```bash
cd backend
uvicorn app.main:app --reload
```

Accéder à la documentation interactive :
- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

### Tester avec Swagger UI :

1. **POST /auth/mock-login**
   - Cliquer sur "Try it out"
   - Entrer email : `test@example.cm`
   - Cliquer "Execute"
   - Copier le `access_token`

2. **Authorize** (bouton en haut)
   - Cliquer sur le cadenas "Authorize"
   - Entrer : `Bearer <votre_token>`
   - Cliquer "Authorize"

3. **GET /auth/me**
   - Cliquer "Try it out"
   - Cliquer "Execute"
   - Voir vos informations marchand

## Sécurité

### Hackathon (Actuel)
- ✅ Auto-signup simplifié (pas de password)
- ✅ JWT avec expiration 1h
- ⚠️ SECRET_KEY par défaut (à changer)

### Production (TODO)
- 🔒 Password hashing (bcrypt)
- 🔒 Email verification
- 🔒 Refresh tokens
- 🔒 Rate limiting
- 🔒 HTTPS obligatoire
- 🔒 SECRET_KEY robuste (généré)
- 🔒 OAuth2 Genuka réel

## Dépannage

### Erreur : 401 Unauthorized

**Cause** : Token invalide, expiré, ou format incorrect

**Solutions** :
- Vérifier format header : `Bearer <token>` (attention à l'espace)
- Vérifier expiration : token expire après 60 minutes
- Refaire login pour obtenir nouveau token
- Vérifier SECRET_KEY est le même partout

### Erreur : Module 'jwt' has no attribute 'JWTError'

**Cause** : Version PyJWT incompatible

**Solution** :
```bash
pip install --upgrade PyJWT==2.8.0
```

### Erreur : 500 Internal Server Error

**Cause** : Base de données non initialisée

**Solution** :
```bash
cd backend
python3 app/database.py  # Créer les tables
```

## Prochaines Étapes

1. **TrustScore API** : Protéger `/trustscores` avec `get_current_merchant`
2. **Documents API** : Upload documents pour le marchand authentifié
3. **Badges API** : Générer badges pour le marchand authentifié
4. **Frontend** : Implémenter login UI avec stockage token

---

**Version** : 1.0.0-hackathon
**Dernière mise à jour** : 5 Décembre 2025
**Auteur** : SmartKYC Team
