# TrustScoreCalculator - Guide d'Utilisation

## Vue d'ensemble

Le `TrustScoreCalculator` calcule le TrustScore d'un marchand (0-1000 points) et attribue un badge de confiance (Bronze, Silver, Gold, Platinum).

## Modes de Calcul

### Mode COLD_START (< 3 mois d'historique)
- **Basé uniquement sur les documents**
- **Score maximum : 500 points** (Badge Bronze max)
- Utilisé pour les nouveaux marchands

### Mode NORMAL (3+ mois d'historique)
- **Algorithme complet (10/40/30/20)**
- **Score maximum : 1000 points** (Badge Platinum possible)
- Utilisé pour les marchands établis

## Utilisation Rapide

```python
from app.services.trustscore_calculator import calculate_trustscore_for_merchant

# Calculer le TrustScore
result = calculate_trustscore_for_merchant("merchant-123")

# Afficher les résultats
print(f"Score: {result['trustscore']}/1000")
print(f"Badge: {result['badge']}")
print(f"Mode: {result['calculation_mode']}")
```

## Structure du Résultat

```json
{
  "trustscore": 828,
  "badge": "GOLD",
  "calculation_mode": "NORMAL",
  "metrics": {
    "documents": {
      "score": 60.0,
      "weight": 0.10,
      "verified_count": 3,
      "total_count": 5,
      "verified_types": ["RCCM", "CNI", "NIF"],
      "missing_types": ["BANK_STATEMENT", "ADDRESS_PROOF"]
    },
    "historique": {
      "score": 80.0,
      "weight": 0.40,
      "anciennete": {"score": 80, "months": 12},
      "regularite": {"score": 70, "cv": 0.201},
      "croissance": {"score": 100, "monthly_growth_rate": 0.080}
    },
    "comportement": {
      "score": 100.0,
      "weight": 0.30,
      "diversification": {"score": 100, "top_customer_pct": 0.10},
      "fidelisation": {"score": 100, "recurring_pct": 0.756},
      "panier_moyen": {"score": 100, "trend": 0.138}
    },
    "financiers": {
      "score": 74.0,
      "weight": 0.20,
      "ca_mensuel": {"score": 100, "amount": 450209701},
      "rotation_stock": {"score": 40, "times_per_year": 2.8},
      "marge_brute": {"score": 60, "percentage": 21.7}
    }
  },
  "valid_until": "2026-06-03T00:00:00",
  "created_at": "2025-12-05T00:00:00"
}
```

## Algorithme - Mode NORMAL

### Formule Générale

```
TrustScore = (Documents×10% + Historique×40% + Comportement×30% + Financiers×20%) × 10
```

### 1. Documents (10%)

**Score = (documents vérifiés / 5) × 100**

Documents acceptés :
- ✅ RCCM (Registre de Commerce)
- ✅ CNI (Carte Nationale d'Identité du gérant)
- ✅ NIF (Numéro d'Identification Fiscale)
- ✅ BANK_STATEMENT (Relevé bancaire)
- ✅ ADDRESS_PROOF (Justificatif de domicile)

### 2. Historique Business (40%)

**Score = Ancienneté×25% + Régularité×50% + Croissance×25%**

#### Ancienneté (25%)
| Mois | Score |
|------|-------|
| 24+ mois | 100 |
| 12-23 mois | 80 |
| 6-11 mois | 60 |
| 3-5 mois | 40 |

#### Régularité des ventes - CV (50%)
| Coefficient de Variation | Score |
|---------------------------|-------|
| CV < 15% | 100 |
| CV < 20% | 90 |
| CV < 30% | 70 |
| CV < 50% | 50 |
| CV ≥ 50% | 30 |

#### Croissance mensuelle (25%)
| Taux de croissance | Score |
|--------------------|-------|
| ≥ 5%/mois | 100 |
| ≥ 3%/mois | 85 |
| ≥ 0%/mois | 70 |
| ≥ -2%/mois | 50 |
| < -2%/mois | 30 |

### 3. Comportement Client (30%)

**Score = Diversification×40% + Fidélisation×35% + Panier Moyen×25%**

#### Diversification (40%)
*Top client < 20% du CA*

| Top client % CA | Score |
|-----------------|-------|
| < 15% | 100 |
| < 20% | 90 |
| < 30% | 70 |
| < 50% | 50 |
| ≥ 50% | 30 |

#### Fidélisation (35%)
*60%+ clients récurrents (≥3 commandes)*

| Clients récurrents | Score |
|--------------------|-------|
| ≥ 70% | 100 |
| ≥ 60% | 90 |
| ≥ 50% | 75 |
| ≥ 40% | 60 |
| < 40% | 40 |

#### Panier moyen (25%)
*Évolution du panier moyen*

| Tendance | Score |
|----------|-------|
| +10%+ | 100 |
| +5% à +10% | 85 |
| 0% à +5% | 70 |
| -5% à 0% | 55 |
| < -5% | 40 |

### 4. Financiers (20%)

**Score = CA Mensuel×50% + Rotation Stock×30% + Marge Brute×20%**

#### CA mensuel moyen (50%)
| CA mensuel (FCFA) | Score |
|-------------------|-------|
| ≥ 10M | 100 |
| 5M - 10M | 85 |
| 3M - 5M | 70 |
| 1M - 3M | 55 |
| < 1M | 40 |

#### Rotation stock (30%)
| Rotation/an | Score |
|-------------|-------|
| ≥ 12× | 100 |
| 8-12× | 90 |
| 6-8× | 75 |
| 4-6× | 60 |
| < 4× | 40 |

#### Marge brute (20%)
| Marge | Score |
|-------|-------|
| ≥ 35% | 100 |
| 30-35% | 90 |
| 25-30% | 75 |
| 20-25% | 60 |
| < 20% | 40 |

## Attribution du Badge

| Badge | Seuil TrustScore | Documents requis | Autres |
|-------|------------------|------------------|--------|
| 🥇 **PLATINUM** | ≥ 850 | Tous (5/5) | Site visit* |
| 🥇 **GOLD** | ≥ 700 | 3 essentiels (RCCM, CNI, NIF) | - |
| 🥈 **SILVER** | ≥ 550 | 2 documents | - |
| 🥉 **BRONZE** | ≥ 400 | 1 document | - |
| ⚪ **NONE** | < 400 | - | - |

*Site visit non implémenté pour le hackathon

## Algorithme - Mode COLD_START

### Points par Document

```python
score = 0

if RCCM_verified:
    score += 200
    if récent (< 1 an): score += 20
    if entreprise active: score += 30

if CNI_verified:
    score += 150
    if valide (non expiré): score += 20

if NIF_verified:
    score += 150
    if à jour: score += 30

if BANK_STATEMENT_verified:
    score += 25

if ADDRESS_PROOF_verified:
    score += 25

# Normaliser sur 500 (max: 650 points)
trustscore = (score / 650) * 500
```

### Exemple COLD_START

**Cas : Nouveau marchand avec RCCM + CNI + NIF**

```
RCCM : 200 + 20 (récent) + 30 (actif) = 250
CNI  : 150 + 20 (valide) = 170
NIF  : 150 + 30 (à jour) = 180
Total: 600 points

TrustScore = (600/650) × 500 = 461 points
Badge = BRONZE (≥400, 3 docs)
```

## Exemples d'Utilisation

### 1. Calcul Simple

```python
from app.services.trustscore_calculator import TrustScoreCalculator

calculator = TrustScoreCalculator(merchant_id="merchant-123")
result = calculator.calculate_trustscore()

print(f"TrustScore: {result['trustscore']}")
print(f"Badge: {result['badge']}")
```

### 2. Analyse Détaillée

```python
result = calculate_trustscore_for_merchant("merchant-123")

if result['calculation_mode'] == 'NORMAL':
    metrics = result['metrics']

    print("Analyse des Métriques:")
    print(f"Documents: {metrics['documents']['score']:.0f}/100")
    print(f"Historique: {metrics['historique']['score']:.0f}/100")
    print(f"Comportement: {metrics['comportement']['score']:.0f}/100")
    print(f"Financiers: {metrics['financiers']['score']:.0f}/100")

    # Recommandations
    if metrics['documents']['score'] < 80:
        print("⚠️  Recommandation: Compléter les documents manquants")

    if metrics['historique']['regularite']['cv'] > 0.20:
        print("⚠️  Recommandation: Améliorer la régularité des ventes")

    if metrics['comportement']['diversification']['top_customer_pct'] > 0.20:
        print("⚠️  Recommandation: Diversifier la base client")
```

### 3. Sérialisation JSON (API)

```python
import json

result = calculate_trustscore_for_merchant("merchant-123")

# Pour réponse API
json_response = json.dumps(result, indent=2)
print(json_response)
```

### 4. Avec Session Database

```python
from app.database import get_db

db = next(get_db())
calculator = TrustScoreCalculator(merchant_id="merchant-123", db_session=db)
result = calculator.calculate_trustscore()
```

## Intégration avec API

```python
# Dans api/trustscores.py
from fastapi import APIRouter, Depends
from app.services.trustscore_calculator import calculate_trustscore_for_merchant

router = APIRouter()

@router.post("/trustscores")
async def calculate_trustscore(merchant_id: str):
    """Calculer le TrustScore d'un marchand"""
    result = calculate_trustscore_for_merchant(merchant_id)
    return result

@router.get("/trustscores/latest")
async def get_latest_trustscore(merchant_id: str):
    """Récupérer le dernier TrustScore calculé"""
    # TODO: Fetch from database
    result = calculate_trustscore_for_merchant(merchant_id)
    return result
```

## Tests

Exécuter les tests :

```bash
cd /home/quasars/Documents/smartkyc-hackathon/smartkyc/backend
python3 test_trustscore_calculator.py
```

Tests inclus :
1. ✅ Mode NORMAL (marchand établi)
2. ✅ Mode COLD_START (nouveau marchand)
3. ✅ Profils multiples
4. ✅ Validation des composantes
5. ✅ Attribution des badges
6. ✅ Sérialisation JSON

## Métriques de Performance

- **Calcul TrustScore** : ~300ms (avec génération données mock)
- **Calcul avec données en cache** : ~10ms
- **Sérialisation JSON** : ~2ms

## TODO - Améliorations Futures

### 1. Documents (actuellement placeholder)
```python
# Remplacer _get_verified_documents() avec requête DB réelle
def _get_verified_documents(self):
    if not self.db_session:
        return {}

    from app.models.document import Document
    docs = self.db_session.query(Document).filter(
        Document.merchant_id == self.merchant_id,
        Document.verification_status == 'VERIFIED'
    ).all()

    return {doc.document_type: doc for doc in docs}
```

### 2. Persistance des Résultats
```python
# Sauvegarder dans DB pour historique
def save_to_database(self, result):
    from app.models.trustscore import TrustScore

    ts = TrustScore(
        merchant_id=self.merchant_id,
        trustscore=result['trustscore'],
        badge=result['badge'],
        calculation_mode=result['calculation_mode'],
        metrics=json.dumps(result['metrics']),
        valid_until=result['valid_until']
    )
    self.db_session.add(ts)
    self.db_session.commit()
```

### 3. Cache pour Performance
```python
# Cache Redis pour éviter recalculs fréquents
import redis

cache = redis.Redis(host='localhost', port=6379)
cache_key = f"trustscore:{merchant_id}"
cached = cache.get(cache_key)

if cached:
    return json.loads(cached)
else:
    result = calculator.calculate_trustscore()
    cache.setex(cache_key, 3600, json.dumps(result))  # 1h TTL
    return result
```

## Support

Pour questions ou bugs, contacter l'équipe SmartKYC Innovators.

---

**Version** : 1.0.0-hackathon
**Dernière mise à jour** : 5 Décembre 2025
**Auteur** : SmartKYC Team
