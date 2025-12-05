# Badge & QR Code System - Setup Guide

## ✅ Implementation Complete

Le système de génération de badges et QR codes est maintenant entièrement implémenté avec :

- **QR Code Generator** ([qr_generator.py](app/services/qr_generator.py))
- **Badge Image Generator** ([badge_generator.py](app/services/badge_generator.py))
- **API Endpoints** ([badges.py](app/api/badges.py))
- **Database Integration** (Badge model avec codes de vérification)
- **4 Niveaux de Badges** : Bronze, Silver, Gold, Platinum

## 🎨 Niveaux de Badges

### Badge Colors

Chaque niveau a des couleurs distinctes :

| Niveau | Couleur Primaire | Score Minimum | Validité |
|--------|------------------|---------------|----------|
| **PLATINUM** | Gris Platinum | 850+ | 6 mois |
| **GOLD** | Or | 700+ | 6 mois |
| **SILVER** | Argent | 550+ | 6 mois |
| **BRONZE** | Bronze | 400+ | 6 mois |
| **NONE** | Gris | < 400 | - |

### Badge Design

Chaque badge (600x400px) affiche :
- **Titre** : "GOLD BADGE", "SILVER BADGE", etc.
- **TrustScore** : 850/1000 (grande police)
- **Nom du Business** : Nom du marchand
- **Branding** : "SmartKYC 2025"
- **Tagline** : "Le Badge de Confiance du B2B Africain"
- **Gradient Background** : Dégradé de couleurs du niveau

## 📱 QR Codes

### Format QR Code

Chaque QR code contient :
```
https://verify.smartkyc.cm/verify/{verification_code}
```

- **verification_code** : UUID unique
- **Taille** : Box size 10, Border 4
- **Error Correction** : Level L (~7%)
- **Format** : PNG

### QR Code avec Logo (Advanced)

La fonction `generate_qr_code_with_logo()` permet d'ajouter un logo au centre du QR code :
- Logo redimensionné à 1/5 de la taille du QR
- Error correction Level H (~30%) pour supporter le logo
- Logo centré automatiquement

## 📡 API Endpoints

### POST /api/badges/generate

Génère un badge pour le marchand authentifié.

**Prérequis** :
- Marchand doit avoir un TrustScore calculé
- Authentification JWT requise

**Request** :
```bash
curl -X POST "http://localhost:8000/api/badges/generate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response** :
```json
{
  "id": "badge-abc-123",
  "merchant_id": "merchant-xyz",
  "badge_level": "GOLD",
  "trustscore": 850,
  "verification_code": "d54556b2-fe45-46e9-83ef-d587d1247690",
  "badge_image_url": "/data/badges/merchant-xyz/badge_gold_850.png",
  "qr_code_url": "/data/qrcodes/merchant-xyz/qr_d54556b2.png",
  "verification_url": "https://verify.smartkyc.cm/verify/d54556b2-fe45-46e9-83ef-d587d1247690",
  "issued_at": "2025-12-05T10:30:00",
  "expires_at": "2026-06-05T10:30:00",
  "is_active": true
}
```

**Comportement** :
- Si un badge actif et valide existe déjà → Retourne le badge existant
- Si le badge a expiré → Désactive l'ancien et crée un nouveau
- Génère QR code + badge image automatiquement
- Sauvegarde dans la base de données

### GET /api/badges/current

Récupère le badge actif du marchand.

**Request** :
```bash
curl -X GET "http://localhost:8000/api/badges/current" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response** :
```json
{
  "id": "badge-abc-123",
  "merchant_id": "merchant-xyz",
  "badge_level": "GOLD",
  "badge_image_path": "/data/badges/...",
  "qr_code_data": "https://verify.smartkyc.cm/verify/...",
  "qr_code_image_path": "/data/qrcodes/...",
  "verification_code": "d54556b2-...",
  "issued_at": "2025-12-05T10:30:00",
  "expires_at": "2026-06-05T10:30:00",
  "is_active": true
}
```

### GET /api/badges/share

Récupère les informations de partage du badge.

**Request** :
```bash
curl -X GET "http://localhost:8000/api/badges/share" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response** :
```json
{
  "verification_code": "d54556b2-fe45-46e9-83ef-d587d1247690",
  "verification_url": "https://verify.smartkyc.cm/verify/d54556b2-...",
  "qr_code_url": "/data/qrcodes/merchant-xyz/qr_d54556b2.png",
  "badge_image_url": "/data/badges/merchant-xyz/badge_gold_850.png",
  "share_message": "🏆 Kouassi Distribution est certifié SmartKYC !\n\n📊 TrustScore: 850/1000\n🥇 Badge: GOLD\n\nVérifiez notre badge de confiance:\nhttps://verify.smartkyc.cm/verify/d54556b2-fe45-46e9-83ef-d587d1247690\n\n#SmartKYC #B2BAfrica #TrustScore"
}
```

### DELETE /api/badges/{badge_id}

Révoque (désactive) un badge.

**Request** :
```bash
curl -X DELETE "http://localhost:8000/api/badges/badge-abc-123" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response** : 204 No Content

**Note** : Le badge n'est pas supprimé de la DB, seulement désactivé (`is_active = false`) pour garder l'historique.

## 📂 Stockage des Fichiers

### Structure

```
backend/data/
  ├── badges/
  │   └── {merchant_id}/
  │       ├── badge_gold_850.png
  │       ├── badge_platinum_920.png
  │       └── ...
  └── qrcodes/
      └── {merchant_id}/
          ├── qr_{verification_code}.png
          ├── qr_logo_{verification_code}.png
          └── ...
```

### Tailles de Fichiers

- **Badge PNG** : ~20-25 KB (600x400px)
- **QR Code PNG** : ~800 bytes (petit, optimisé)

## 🚀 Workflow Complet

### 1. Login
```bash
curl -X POST "http://localhost:8000/auth/mock-login" \
  -H "Content-Type: application/json" \
  -d '{"email": "merchant@example.cm"}'
```

### 2. Calculate TrustScore
```bash
curl -X POST "http://localhost:8000/api/trustscores/calculate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Response : `{"trustscore": 850, "badge": "GOLD", ...}`

### 3. Generate Badge
```bash
curl -X POST "http://localhost:8000/api/badges/generate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Response : Badge + QR code URLs

### 4. Share Badge

Utilisez le `verification_url` ou le QR code pour partager :
- Sur les réseaux sociaux
- Dans la signature email
- Sur le site web de l'entreprise
- Sur les cartes de visite

### 5. Verification (Public)

N'importe qui peut scanner le QR code ou visiter l'URL pour vérifier le badge :
```
https://verify.smartkyc.cm/verify/{verification_code}
```

Cette page affichera :
- Nom du marchand
- TrustScore
- Badge level
- Documents vérifiés
- Recommandation de crédit
- Date d'émission et expiration

## 🧪 Testing

### Run Tests
```bash
cd /home/quasars/Documents/smartkyc-hackathon/smartkyc/backend
python3 test_badge_api.py
```

### Test Results
```
Total: 5/5 tests passed
✅ QR Code Generation
✅ Badge Image Generation
✅ Badge Database Integration
✅ Badge API Workflow
✅ Badge Colors and Levels
```

### Manual Testing with Images

Les tests génèrent de vraies images de badges que vous pouvez visualiser :

```bash
# Générer un badge Gold de test
python3 -c "
from app.services.badge_generator import BadgeGenerator
gen = BadgeGenerator()
path = gen.generate_badge('GOLD', 850, 'Kouassi Distribution SARL')
print(f'Badge créé : {path}')
"

# Générer un QR code de test
python3 -c "
from app.services.qr_generator import QRCodeGenerator
gen = QRCodeGenerator()
path = gen.generate_qr_code('test-verification-code-123')
print(f'QR code créé : {path}')
"
```

## 🎨 Personnalisation

### Changer les Couleurs de Badge

Editez `badge_generator.py` :

```python
BADGE_COLORS = {
    'GOLD': {
        'primary': (255, 215, 0),     # Couleur principale
        'secondary': (255, 235, 59),  # Couleur secondaire (gradient)
        'text': (33, 33, 33),         # Couleur du texte
        'accent': (255, 193, 7)       # Couleur des accents
    },
    # ...
}
```

### Changer la Taille du Badge

```python
BADGE_WIDTH = 800   # Default: 600
BADGE_HEIGHT = 600  # Default: 400
```

### Changer l'URL de Vérification

Dans `qr_generator.py` :

```python
BASE_VERIFICATION_URL = "https://votre-domaine.com/verify"
```

Ou via l'API :
```python
generator = QRCodeGenerator()
generator.set_verification_url("https://votre-domaine.com/verify")
```

## 📊 Base de Données

### Table badges

```sql
CREATE TABLE badges (
    id VARCHAR(36) PRIMARY KEY,
    merchant_id VARCHAR(36) NOT NULL,
    badge_level ENUM('BRONZE', 'SILVER', 'GOLD', 'PLATINUM'),
    badge_image_path VARCHAR(500),
    qr_code_data TEXT,
    qr_code_image_path VARCHAR(500),
    verification_code VARCHAR(36) UNIQUE NOT NULL,
    issued_at DATETIME NOT NULL,
    expires_at DATETIME NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (merchant_id) REFERENCES merchants(id)
);
```

### Requêtes Utiles

```sql
-- Trouver tous les badges actifs
SELECT * FROM badges WHERE is_active = TRUE;

-- Trouver les badges expirés
SELECT * FROM badges WHERE expires_at < NOW() AND is_active = TRUE;

-- Compter les badges par niveau
SELECT badge_level, COUNT(*)
FROM badges
WHERE is_active = TRUE
GROUP BY badge_level;

-- Historique des badges d'un marchand
SELECT * FROM badges
WHERE merchant_id = 'merchant-xyz'
ORDER BY issued_at DESC;
```

## 🔒 Sécurité

### Codes de Vérification

- **UUID v4** : Codes uniques non prédictibles
- **Uniques** : Constraint UNIQUE sur `verification_code`
- **Validité** : 6 mois (180 jours)
- **Expiration** : Vérifiée côté serveur

### Badge Actif

- 1 seul badge actif par marchand à la fois
- Les anciens badges restent en DB mais `is_active = false`
- Permet l'historique et l'audit

### Révocation

- Les badges peuvent être révoqués via DELETE endpoint
- La révocation est immédiate (`is_active = false`)
- Le QR code devient invalide

## 🎯 Pour le Hackathon

### Démo Preparation

1. **Créer 5 profils tests** avec différents niveaux :
```python
# Bronze (450), Silver (600), Gold (750), Platinum (900)
```

2. **Imprimer les QR codes** sur cartes de visite

3. **Préparer screenshots** des badges pour la présentation

4. **Tester le scan** sur 3 smartphones différents

### Workflow Démo (2 minutes)

1. **Login** → Merchant dashboard
2. **Calculate TrustScore** → Affiche 850/1000, Gold
3. **Generate Badge** → Badge + QR code créés
4. **Show Badge** → Belle image Gold visible
5. **Scan QR** → Juge scanne avec son téléphone
6. **Verification Page** → Informations s'affichent (mobile-friendly)
7. **Wow Effect** → "C'est instantané et professionnel !"

## 📝 Next Steps

Selon [CLAUDE.md](CLAUDE.md), il reste :

1. **Page de Vérification Publique** (`api/verify.py`)
   - `GET /verify/{code}` - Page HTML (pas d'auth)
   - Affichage du badge, TrustScore, documents
   - Mobile-first responsive design

Le backend est maintenant à **~90% complet** pour le hackathon MVP ! 🎉

## 📞 Support

**Files Created:**
- ✅ [app/services/qr_generator.py](app/services/qr_generator.py) - QR code generation
- ✅ [app/services/badge_generator.py](app/services/badge_generator.py) - Badge image generation
- ✅ [app/schemas/badge.py](app/schemas/badge.py) - Pydantic schemas
- ✅ [app/api/badges.py](app/api/badges.py) - API endpoints
- ✅ [test_badge_api.py](test_badge_api.py) - Test suite

**Dependencies:**
- `qrcode[pil]` - Déjà dans requirements.txt
- `Pillow` - Déjà installé
- Fonts: DejaVu Sans (system fonts)

---

**Last Updated:** 2025-12-05
**Status:** ✅ Ready for Integration
**Tests:** 5/5 Passed
