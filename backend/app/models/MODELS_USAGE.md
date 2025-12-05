# SmartKYC - SQLAlchemy Models Guide

## Vue d'ensemble

Les modèles SQLAlchemy définissent la structure de la base de données et les relations entre les entités du système SmartKYC.

## Architecture des Modèles

```
Base (base.py)
  │
  ├── Merchant (merchant.py)
  │   ├── TrustScore[] (trustscore.py) - one-to-many
  │   ├── Document[] (document.py) - one-to-many
  │   ├── Badge (badge.py) - one-to-one
  │   └── Verification[] (verification.py) - one-to-many
  │
  └── Relations avec CASCADE DELETE
```

## Modèles Disponibles

### 1. Merchant (merchants)

**Description** : Représente un compte marchand.

**Attributs** :
```python
id: str                           # UUID unique
genuka_merchant_id: str           # ID Genuka (unique)
email: str                        # Email (unique, indexé)
business_name: str                # Nom de l'entreprise
access_token: str                 # Token OAuth Genuka
token_expires_at: datetime        # Expiration du token
subscription_tier: SubscriptionTier  # FREE, BASIC, PRO, ENTERPRISE
subscription_ends_at: datetime    # Fin de l'abonnement
created_at: datetime              # Date de création
updated_at: datetime              # Dernière mise à jour
```

**Relations** :
- `trustscores` : List[TrustScore] (one-to-many)
- `documents` : List[Document] (one-to-many)
- `badge` : Badge (one-to-one)
- `verifications` : List[Verification] (one-to-many)

**Utilisation** :
```python
from app.models import Merchant, SubscriptionTier
import uuid

# Créer un marchand
merchant = Merchant(
    id=str(uuid.uuid4()),
    email="kouassi@example.cm",
    business_name="Kouassi Distribution",
    subscription_tier=SubscriptionTier.FREE
)

db.add(merchant)
db.commit()

# Convertir en dict
merchant_dict = merchant.to_dict()
```

### 2. TrustScore (trustscores)

**Description** : Stocke les calculs de TrustScore.

**Attributs** :
```python
id: str                          # UUID unique
merchant_id: str                 # FK → merchants.id
trustscore: int                  # Score 0-1000
badge: BadgeLevel                # NONE, BRONZE, SILVER, GOLD, PLATINUM
metrics: str                     # JSON des métriques détaillées
calculation_mode: CalculationMode  # COLD_START ou NORMAL
valid_until: datetime            # Date d'expiration (6 mois)
created_at: datetime             # Date de calcul
```

**Relations** :
- `merchant` : Merchant (many-to-one)

**Méthodes** :
```python
get_metrics() -> dict           # Parse JSON metrics
set_metrics(dict) -> None       # Définir metrics depuis dict
to_dict() -> dict               # Convertir en dict
```

**Utilisation** :
```python
from app.models import TrustScore, TrustScoreBadgeLevel, CalculationMode
from datetime import datetime, timedelta
import uuid
import json

# Créer un TrustScore
trustscore = TrustScore(
    id=str(uuid.uuid4()),
    merchant_id=merchant.id,
    trustscore=828,
    badge=TrustScoreBadgeLevel.GOLD,
    calculation_mode=CalculationMode.NORMAL,
    valid_until=datetime.utcnow() + timedelta(days=180)
)

# Définir les métriques
metrics = {
    "documents": {"score": 60.0, "weight": 0.10},
    "historique": {"score": 80.0, "weight": 0.40},
    "comportement": {"score": 100.0, "weight": 0.30},
    "financiers": {"score": 74.0, "weight": 0.20}
}
trustscore.set_metrics(metrics)

db.add(trustscore)
db.commit()

# Récupérer les métriques
metrics_dict = trustscore.get_metrics()
```

### 3. Document (documents)

**Description** : Stocke les documents uploadés pour vérification.

**Attributs** :
```python
id: str                          # UUID unique
merchant_id: str                 # FK → merchants.id
document_type: DocumentType      # RCCM, CNI, NIF, BANK_STATEMENT, ADDRESS_PROOF
filename: str                    # Nom du fichier original
filepath: str                    # Chemin de stockage
file_size: int                   # Taille en octets
verification_status: VerificationStatus  # PENDING, VERIFIED, REJECTED
verified_at: datetime            # Date de vérification
extracted_data: str              # JSON des données OCR
uploaded_at: datetime            # Date d'upload
```

**Contrainte** : Un marchand ne peut avoir qu'un document de chaque type (unique_merchant_doc).

**Relations** :
- `merchant` : Merchant (many-to-one)

**Méthodes** :
```python
get_extracted_data() -> dict    # Parse JSON extracted_data
set_extracted_data(dict) -> None  # Définir extracted_data depuis dict
mark_verified() -> None         # Marquer comme VERIFIED
mark_rejected() -> None         # Marquer comme REJECTED
to_dict() -> dict               # Convertir en dict
```

**Utilisation** :
```python
from app.models import Document, DocumentType, VerificationStatus
import uuid

# Upload d'un document
document = Document(
    id=str(uuid.uuid4()),
    merchant_id=merchant.id,
    document_type=DocumentType.RCCM,
    filename="rccm_kouassi.pdf",
    filepath="/data/uploads/merchant-123/RCCM/rccm_kouassi.pdf",
    file_size=1024000,
    verification_status=VerificationStatus.PENDING
)

db.add(document)
db.commit()

# Après OCR
ocr_data = {
    "company_name": "Kouassi Distribution",
    "rccm_number": "CM-YAO-2020-B-12345",
    "registration_date": "2020-03-15"
}
document.set_extracted_data(ocr_data)

# Marquer comme vérifié
document.mark_verified()
db.commit()
```

### 4. Badge (badges)

**Description** : Badge de confiance généré pour un marchand.

**Attributs** :
```python
id: str                          # UUID unique
merchant_id: str                 # FK → merchants.id (unique, one-to-one)
badge_level: BadgeLevel          # BRONZE, SILVER, GOLD, PLATINUM
badge_image_path: str            # Chemin de l'image du badge
qr_code_data: str                # Données du QR code
qr_code_image_path: str          # Chemin de l'image QR
verification_code: str           # Code de vérification unique
issued_at: datetime              # Date d'émission
expires_at: datetime             # Date d'expiration (6 mois)
is_active: bool                  # Badge actif ou non
```

**Relations** :
- `merchant` : Merchant (one-to-one)

**Méthodes** :
```python
is_valid() -> bool              # Vérifie si badge est valide (actif et non expiré)
deactivate() -> None            # Désactiver le badge
activate() -> None              # Activer le badge
to_dict() -> dict               # Convertir en dict
```

**Utilisation** :
```python
from app.models import Badge, BadgeLevel
from datetime import datetime, timedelta
import uuid
import secrets

# Générer un badge
badge = Badge(
    id=str(uuid.uuid4()),
    merchant_id=merchant.id,
    badge_level=BadgeLevel.GOLD,
    qr_code_data=f"https://verify.smartkyc.cm/{verification_code}",
    verification_code=secrets.token_urlsafe(16),
    issued_at=datetime.utcnow(),
    expires_at=datetime.utcnow() + timedelta(days=180),
    is_active=True
)

db.add(badge)
db.commit()

# Vérifier validité
if badge.is_valid():
    print("Badge valide!")

# Désactiver si nécessaire
badge.deactivate()
db.commit()
```

### 5. Verification (verifications)

**Description** : Suivi des visualisations de badge (analytics).

**Attributs** :
```python
id: str                          # UUID unique
merchant_id: str                 # FK → merchants.id
viewer_email: str                # Email du visiteur (optionnel)
viewer_ip: str                   # IP du visiteur
viewed_at: datetime              # Date de visualisation
user_agent: str                  # User agent du navigateur
```

**Relations** :
- `merchant` : Merchant (many-to-one)

**Utilisation** :
```python
from app.models import Verification
import uuid

# Enregistrer une visualisation
verification = Verification(
    id=str(uuid.uuid4()),
    merchant_id=merchant.id,
    viewer_email="supplier@example.cm",
    viewer_ip="192.168.1.100",
    user_agent="Mozilla/5.0..."
)

db.add(verification)
db.commit()
```

## Configuration de la Base de Données

### Fichier : `app/database.py`

```python
from app.database import engine, SessionLocal, get_db, init_db

# Créer les tables (à faire une fois)
init_db()

# Utiliser dans FastAPI
from fastapi import Depends
from sqlalchemy.orm import Session

@app.get("/merchants")
def get_merchants(db: Session = Depends(get_db)):
    merchants = db.query(Merchant).all()
    return [m.to_dict() for m in merchants]
```

## Opérations CRUD

### Créer (Create)

```python
from app.models import Merchant
from app.database import SessionLocal
import uuid

db = SessionLocal()

merchant = Merchant(
    id=str(uuid.uuid4()),
    email="new@example.cm",
    business_name="New Business"
)

db.add(merchant)
db.commit()
db.refresh(merchant)  # Récupère les valeurs auto-générées

print(merchant.id)
db.close()
```

### Lire (Read)

```python
# Récupérer un marchand par ID
merchant = db.query(Merchant).filter(Merchant.id == "merchant-id").first()

# Récupérer par email
merchant = db.query(Merchant).filter(Merchant.email == "test@example.cm").first()

# Récupérer tous les marchands
merchants = db.query(Merchant).all()

# Avec relations (eager loading)
from sqlalchemy.orm import joinedload

merchant = db.query(Merchant)\
    .options(joinedload(Merchant.trustscores))\
    .filter(Merchant.id == "merchant-id")\
    .first()

# Accéder aux relations
for ts in merchant.trustscores:
    print(ts.trustscore, ts.badge.value)
```

### Mettre à jour (Update)

```python
merchant = db.query(Merchant).filter(Merchant.id == "merchant-id").first()

merchant.business_name = "Updated Name"
merchant.subscription_tier = SubscriptionTier.PRO

db.commit()
db.refresh(merchant)
```

### Supprimer (Delete)

```python
# Suppression simple
merchant = db.query(Merchant).filter(Merchant.id == "merchant-id").first()
db.delete(merchant)
db.commit()

# Cascade delete : supprimera aussi tous les trustscores, documents, badge, verifications
```

## Requêtes Avancées

### Filtres et tri

```python
# Filtrer les marchands PRO
pro_merchants = db.query(Merchant)\
    .filter(Merchant.subscription_tier == SubscriptionTier.PRO)\
    .all()

# Trier par date de création
recent_merchants = db.query(Merchant)\
    .order_by(Merchant.created_at.desc())\
    .limit(10)\
    .all()

# Recherche par email pattern
merchants = db.query(Merchant)\
    .filter(Merchant.email.like("%@gmail.com"))\
    .all()
```

### Jointures

```python
from sqlalchemy import func

# Compter les documents par marchand
result = db.query(
    Merchant.business_name,
    func.count(Document.id).label('doc_count')
)\
.join(Document)\
.group_by(Merchant.id)\
.all()

for name, count in result:
    print(f"{name}: {count} documents")
```

### Dernier TrustScore

```python
# Récupérer le dernier TrustScore d'un marchand
latest_trustscore = db.query(TrustScore)\
    .filter(TrustScore.merchant_id == merchant.id)\
    .order_by(TrustScore.created_at.desc())\
    .first()
```

## Énumérations (Enums)

### SubscriptionTier
- `FREE` : Gratuit
- `BASIC` : Basique
- `PRO` : Professionnel
- `ENTERPRISE` : Entreprise

### BadgeLevel
- `BRONZE` : Bronze (400-549)
- `SILVER` : Argent (550-699)
- `GOLD` : Or (700-849)
- `PLATINUM` : Platine (850+)

### CalculationMode
- `COLD_START` : Nouveau marchand (< 3 mois)
- `NORMAL` : Marchand établi (3+ mois)

### DocumentType
- `RCCM` : Registre de Commerce
- `CNI` : Carte Nationale d'Identité
- `NIF` : Numéro d'Identification Fiscale
- `BANK_STATEMENT` : Relevé bancaire
- `ADDRESS_PROOF` : Justificatif de domicile

### VerificationStatus
- `PENDING` : En attente
- `VERIFIED` : Vérifié
- `REJECTED` : Rejeté

## Gestion des Erreurs

```python
from sqlalchemy.exc import IntegrityError

try:
    merchant = Merchant(
        id=str(uuid.uuid4()),
        email="duplicate@example.cm",  # Email existe déjà
        business_name="Test"
    )
    db.add(merchant)
    db.commit()
except IntegrityError as e:
    db.rollback()
    print("Erreur : Email déjà utilisé")
```

## Migrations (Alembic)

Pour la production, utilisez Alembic pour gérer les migrations :

```bash
# Initialiser Alembic
alembic init alembic

# Créer une migration
alembic revision --autogenerate -m "Add new column"

# Appliquer les migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Tests

Exécuter les tests des modèles :

```bash
cd /home/quasars/Documents/smartkyc-hackathon/smartkyc/backend
python3 test_models.py
```

## Diagramme des Relations

```
┌─────────────┐
│  Merchant   │
└──────┬──────┘
       │
       ├─────────┬──────────┬──────────┬───────────┐
       │         │          │          │           │
       ▼         ▼          ▼          ▼           ▼
  ┌──────┐  ┌────────┐  ┌────────┐  ┌───────┐  ┌──────────┐
  │Badge │  │Document│  │TrustSc.│  │Verif. │  │(more...)│
  │(1:1) │  │(1:N)   │  │(1:N)   │  │(1:N)  │  │         │
  └──────┘  └────────┘  └────────┘  └───────┘  └──────────┘
```

## Support

Pour questions ou bugs, consultez l'équipe SmartKYC Innovators.

---

**Version** : 1.0.0-hackathon
**Dernière mise à jour** : 5 Décembre 2025
**Auteur** : SmartKYC Team
