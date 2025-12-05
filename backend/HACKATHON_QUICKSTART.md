# 🏆 SmartKYC - Hackathon Quickstart Guide

**Pour : Hackathon Genuka 4-6 Décembre 2025**
**Équipe : SmartKYC Innovators**

---

## ⚡ Démarrage Ultra-Rapide (5 minutes)

### Prérequis

```bash
# Vérifier Python 3.11+
python3 --version

# Vérifier MySQL
mysql --version
```

### Installation

```bash
# 1. Aller dans le dossier backend
cd /home/quasars/Documents/smartkyc-hackathon/smartkyc/backend

# 2. Installer dépendances Python
pip install -r requirements.txt

# 3. Installer Tesseract OCR (si pas déjà fait)
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-fra tesseract-ocr-eng

# 4. Vérifier .env existe
cat .env
```

### Lancer le Serveur

```bash
# Démarrer FastAPI
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

✅ Serveur lancé sur : http://localhost:8000

### Test Rapide

```bash
# Dans un autre terminal

# Test santé
curl http://localhost:8000/health

# Test logo
curl -I http://localhost:8000/static/logo.png

# Test documentation interactive
# Ouvrir navigateur: http://localhost:8000/docs
```

---

## 🎯 Workflow Démo Hackathon

### Étape 1 : Créer un Marchand

```bash
# Login (auto-signup)
curl -X POST http://localhost:8000/auth/mock-login \
  -H "Content-Type: application/json" \
  -d '{"email": "kouassi@example.cm"}'

# Copier le access_token de la réponse
export TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### Étape 2 : Calculer TrustScore

```bash
curl -X POST http://localhost:8000/api/trustscores/calculate \
  -H "Authorization: Bearer $TOKEN"

# Response: {"trustscore": 850, "badge": "GOLD", ...}
```

### Étape 3 : Générer Badge + QR Code

```bash
curl -X POST http://localhost:8000/api/badges/generate \
  -H "Authorization: Bearer $TOKEN"

# Response: {
#   "verification_code": "abc-123-def-...",
#   "verification_url": "https://verify.smartkyc.cm/verify/abc-123..."
# }
```

### Étape 4 : Vérifier le Badge

```bash
# Copier le verification_code
export CODE="abc-123-def-..."

# Ouvrir dans navigateur (ou scanner QR avec smartphone)
# http://localhost:8000/verify/$CODE
```

**🎉 Démo complète en 4 commandes !**

---

## 📱 Commandes Utiles

### Créer 5 Profils Tests

```bash
# Script Python pour créer profils tests
python3 << 'EOF'
import requests

base_url = "http://localhost:8000"

profils = [
    {"email": "kouassi@example.cm", "name": "Kouassi Distribution"},
    {"email": "marie@example.cm", "name": "Marie Import-Export"},
    {"email": "abdou@example.cm", "name": "Abdou Trading"},
    {"email": "jean@example.cm", "name": "Jean Nouveau"},
    {"email": "sarah@example.cm", "name": "Sarah Premium"}
]

for profil in profils:
    # Login
    r = requests.post(f"{base_url}/auth/mock-login", json={"email": profil["email"]})
    token = r.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    # Calculate TrustScore
    requests.post(f"{base_url}/api/trustscores/calculate", headers=headers)

    # Generate Badge
    r = requests.post(f"{base_url}/api/badges/generate", headers=headers)
    code = r.json()["verification_code"]

    print(f"✅ {profil['name']}: http://localhost:8000/verify/{code}")

print("\n🎉 5 profils créés et prêts pour la démo !")
EOF
```

### Uploader un Document (avec fichier)

```bash
# Exemple avec RCCM
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/rccm.jpg" \
  -F "document_type=RCCM"
```

### Voir Historique TrustScore

```bash
curl -X GET http://localhost:8000/api/trustscores/history \
  -H "Authorization: Bearer $TOKEN"
```

### Obtenir Infos de Partage

```bash
curl -X GET http://localhost:8000/api/badges/share \
  -H "Authorization: Bearer $TOKEN"

# Response contient le message pré-formaté pour réseaux sociaux
```

---

## 🎨 URLs Importantes

| URL | Description |
|-----|-------------|
| http://localhost:8000 | API root |
| http://localhost:8000/docs | Documentation interactive (Swagger) |
| http://localhost:8000/redoc | Documentation alternative (ReDoc) |
| http://localhost:8000/health | Health check |
| http://localhost:8000/static/logo.png | Logo SmartKYC |
| http://localhost:8000/verify/{code} | Page de vérification publique |

---

## 🔧 Commandes Maintenance

### Voir Logs

```bash
# Logs serveur FastAPI
# (Affichés dans le terminal où uvicorn tourne)

# Filtrer logs erreurs seulement
uvicorn app.main:app --log-level error
```

### Reset Database

```bash
# Se connecter à MySQL
mysql -u smartkyc_user -p smartkyc_db

# Voir toutes les tables
SHOW TABLES;

# Compter les merchants
SELECT COUNT(*) FROM merchants;

# Vider une table (attention !)
TRUNCATE TABLE badges;

# Supprimer un merchant spécifique
DELETE FROM merchants WHERE email = 'test@example.cm';
```

### Nettoyer Fichiers Générés

```bash
# Supprimer badges générés
rm -rf data/badges/*

# Supprimer QR codes
rm -rf data/qrcodes/*

# Supprimer documents uploadés
rm -rf data/uploads/*

# Recréer structure
mkdir -p data/badges data/qrcodes data/uploads
```

---

## 🎤 Script Présentation Hackathon

### Slide 1 : Problème (30 secondes)

```
"77% des PME camerounaises n'ont pas accès au crédit.
Pourquoi ?

Les fournisseurs ne font pas confiance.
Vérifier un client prend 7 à 10 jours.

C'est trop long. C'est coûteux. C'est frustrant."
```

### Slide 2 : Solution (30 secondes)

```
"SmartKYC résout ce problème en 10 secondes.

Comment ?

Un TrustScore algorithmique basé sur vos ventes Genuka.
Un badge vérifiable par QR Code.
Une vérification instantanée."
```

### Slide 3 : Démo Live (1 minute)

```
[Écran partagé : Laptop + Smartphone]

"Regardez. Je suis Kouassi Distribution.
J'ai un TrustScore de 850/1000.

[Clic] Je génère mon badge.
[Smartphone] Le fournisseur scanne mon QR Code.

2 secondes plus tard...

[Smartphone affiche la page]

Le fournisseur voit :
- Mon TrustScore : 850
- Mon badge : GOLD
- Mes documents vérifiés
- Recommandation : Crédit jusqu'à 800,000 FCFA

Temps total : 10 secondes vs 7 jours !

Le fournisseur décide : OUI, je lui fais crédit."
```

### Slide 4 : Impact (30 secondes)

```
"Avec SmartKYC :

- Temps de vérification : 7 jours → 10 secondes
- Coût : 5,000 FCFA → GRATUIT
- Accès au crédit : 23% → 80%

C'est un win-win :
- Marchands : Plus de crédit
- Fournisseurs : Moins de risque
- Économie : Plus de croissance"
```

### Slide 5 : Business Model (30 secondes)

```
"Comment on gagne de l'argent ?

Freemium :
- Free : Badge Bronze (gratuit à vie)
- Premium : 5,000 FCFA/mois
  → Badge Gold/Platinum
  → Analytics avancées
  → Support prioritaire

Marché : 100,000 PME au Cameroun
ARR Potentiel : 51.6M FCFA

On commence par le Cameroun.
Ensuite : Côte d'Ivoire, Sénégal, toute l'Afrique."
```

### Slide 6 : Équipe & Appel à l'Action (30 secondes)

```
"L'équipe SmartKYC :
- Prince : PM & Dev
- Marie : Backend
- Jean : Frontend
- Sarah : UI/UX

On a construit un MVP fonctionnel en 72 heures.

Backend : 100% complet
Frontend : 80% complet
Démo : Vous venez de la voir !

Nous voulons gagner ce hackathon pour :
1. Développer la solution complète
2. Lancer au Cameroun en Q1 2026
3. Aider 10,000 PME dans la première année

Merci !"

[Applaudissements]
```

---

## 🐛 Troubleshooting

### Port 8000 déjà utilisé

```bash
# Trouver le processus
lsof -i :8000

# Tuer le processus
kill -9 PID

# Ou utiliser un autre port
uvicorn app.main:app --reload --port 8001
```

### MySQL Connection Error

```bash
# Vérifier que MySQL tourne
sudo systemctl status mysql

# Redémarrer MySQL
sudo systemctl restart mysql

# Vérifier credentials dans .env
cat .env | grep DATABASE_URL
```

### Tesseract Non Installé

```bash
# Installer Tesseract
sudo apt-get install tesseract-ocr tesseract-ocr-fra

# Vérifier installation
tesseract --version
```

### Module Not Found

```bash
# Réinstaller dépendances
pip install -r requirements.txt --upgrade

# Vérifier installation
pip list | grep fastapi
pip list | grep sqlalchemy
```

---

## 📊 Checklist Pré-Démo

### J-1 (Veille de la Démo)

- [ ] Serveur FastAPI démarre sans erreur
- [ ] 5 profils tests créés
- [ ] QR codes imprimés sur cartes
- [ ] Smartphone chargé à 100%
- [ ] Laptop chargé à 100%
- [ ] Connexion Internet stable
- [ ] Slides présentation finalisées
- [ ] Vidéo backup enregistrée
- [ ] Répétition démo 10× (chrono 2 min)

### H-1 (1 heure avant)

- [ ] Serveur démarré
- [ ] Test rapide avec 1 profil
- [ ] QR code scanne correctement
- [ ] Page mobile s'affiche bien
- [ ] Backup plan prêt (vidéo)

### Pendant la Démo

- [ ] Rester calme et confiant
- [ ] Parler lentement et clairement
- [ ] Montrer l'écran à la caméra
- [ ] Smile ! 😊
- [ ] Timer : Max 3 minutes

---

## 🎁 Bonus : One-Liners

### Créer 1000 Merchants de Test

```bash
python3 -c "
import requests
for i in range(1000):
    r = requests.post('http://localhost:8000/auth/mock-login',
                     json={'email': f'merchant{i}@test.cm'})
    if i % 100 == 0: print(f'✅ {i} merchants créés')
"
```

### Benchmark Performance

```bash
# Installer wrk
sudo apt-get install wrk

# Test 10 secondes, 4 threads, 100 connexions
wrk -t4 -c100 -d10s http://localhost:8000/health

# Résultat attendu : > 1000 req/sec
```

### Export Database

```bash
# Exporter toute la DB
mysqldump -u smartkyc_user -p smartkyc_db > backup_$(date +%Y%m%d).sql

# Importer
mysql -u smartkyc_user -p smartkyc_db < backup_20251205.sql
```

---

## 🏁 Conclusion

**Ce guide contient TOUT ce dont vous avez besoin pour :**

✅ Démarrer le serveur en 5 minutes
✅ Créer des profils tests
✅ Faire une démo impeccable
✅ Présenter devant les juges
✅ Gérer les problèmes techniques

**Derniers conseils :**

1. **Testez TOUT avant** la présentation
2. **Ayez un backup** (vidéo de démo)
3. **Restez calme** même si ça bug
4. **Soyez passionnés** - Vous croyez en SmartKYC !
5. **Amusez-vous** - C'est un hackathon ! 🎉

---

**Bon courage et GAGNEZ CE HACKATHON ! 🏆**

**SmartKYC - Le Badge de Confiance du B2B Africain** 🇨🇲

---

**Contact Équipe** :
- Prince (PM) : +237 XXX XXX XXX
- Support : smartkyc@example.cm
- GitHub : github.com/smartkyc

**Hackathon Genuka**
📅 4-6 Décembre 2025
📍 Douala, Cameroun

🚀 **LET'S WIN THIS!**
