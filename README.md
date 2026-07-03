# Projet Machine Learning avec Docker Multi-Stage

Dans ce projet, nous avons :

* un **Backend FastAPI** qui charge un modèle de Machine Learning ;
* un **Frontend Streamlit** qui appelle le backend ;
* un seul **Dockerfile** partagé par les deux services.

Architecture :

```text
Navigateur
      ↓
Frontend (Streamlit)
      ↓
Backend (FastAPI)
      ↓
Modèle ML (.joblib)
```

---

# Pourquoi utiliser le Multi-Stage ?

Sans multi-stage :

```text
Dockerfile Backend
Dockerfile Frontend
```

Les deux fichiers contiennent souvent beaucoup de code identique :

* installation de Debian ;
* installation de uv ;
* configuration Python ;
* variables d'environnement.

Cela crée :

* de la duplication ;
* plus de maintenance ;
* plus de risques d'erreurs.

---

# Avec le Multi-Stage

```text
Stage base
├── Debian
├── uv
└── Configuration Python
       ↓
       ├── Stage backend
       └── Stage frontend
```

Le code commun est écrit une seule fois.

---

# Avantages du Multi-Stage

## Moins de duplication

Le code partagé est centralisé dans :

```text
Stage base
```

---

## Maintenance plus simple

Exemple :

Installation de `uv` :

```text
1 seule modification
      ↓
Backend mis à jour
Frontend mis à jour
```

---

## Construction plus rapide

Docker réutilise les couches communes :

```text
Debian          ✔ Cache
uv              ✔ Cache
Configuration   ✔ Cache
```

---

## Images plus propres

Chaque service ne contient que ce dont il a besoin :

```text
Backend
└── Code Backend
```

```text
Frontend
└── Code Frontend
```

---

# Structure du projet

```text
projet-ml/
├── Dockerfile
├── docker-compose.yml
├── artifacts/
│   └── flight_price_model.joblib
├── backend/
│   ├── pyproject.toml
│   ├── uv.lock
│   └── main.py
└── frontend/
    ├── pyproject.toml
    ├── uv.lock
    └── main.py
```

---

# Stage Base

```dockerfile
FROM debian:bookworm-slim AS base
```

Création d'un stage nommé :

```text
base
```

Ce stage contient tous les éléments communs.

---

# WORKDIR

```dockerfile
WORKDIR /app
```

Crée le dossier :

```text
/app
```

Toutes les commandes suivantes seront exécutées dans ce dossier.

---

# Installation des paquets Linux

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*
```

Installe :

```text
ca-certificates
```

Puis :

```bash
rm -rf /var/lib/apt/lists/*
```

supprime le cache d'installation.

Avantage :

```text
Image plus légère
```

---

# Installation de uv

```dockerfile
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
```

Rend disponibles :

```text
uv
uvx
```

pour tous les stages suivants.

---

# Variables d'environnement

```dockerfile
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=auto
```

Ces variables seront héritées par :

```text
backend
frontend
```

---

# Stage Backend

```dockerfile
FROM base AS backend
```

Le backend hérite automatiquement de :

* Debian ;
* uv ;
* configuration Python.

---

# Installation des dépendances

```dockerfile
COPY backend/pyproject.toml backend/uv.lock ./

RUN uv sync --frozen --no-install-project --no-dev
```

Installe uniquement :

```text
Dépendances de production
```

Les outils de développement ne sont pas installés.

---

# Copie du code backend

```dockerfile
COPY backend/ .
```

Copie :

```text
backend/
├── main.py
├── app/
└── ...
```

vers :

```text
/app
```

---

# Copie du modèle Machine Learning

```dockerfile
COPY artifacts/flight_price_model.joblib /app/artifacts/flight_price_model.joblib
```

Ajoute le modèle entraîné :

```text
flight_price_model.joblib
```

Le backend pourra le charger :

```text
FastAPI
      ↓
Modèle ML
      ↓
Prédiction
```

---

# Démarrage du backend

```dockerfile
CMD ["uv", "run", "uvicorn", "main:app"]
```

Au démarrage :

```bash
uv run uvicorn main:app
```

Le backend expose une API de prédiction.

---

# Stage Frontend

```dockerfile
FROM base AS frontend
```

Le frontend hérite également du stage :

```text
base
```

---

# Installation des dépendances

```dockerfile
COPY frontend/pyproject.toml frontend/uv.lock ./

RUN uv sync --frozen --no-install-project --no-dev
```

Installe uniquement les dépendances nécessaires au frontend.

---

# Copie du code frontend

```dockerfile
COPY frontend/ .
```

Copie :

```text
frontend/
├── main.py
└── ...
```

dans :

```text
/app
```

---

# Démarrage du frontend

```dockerfile
CMD ["uv", "run", "streamlit", "run", "main.py"]
```

Au démarrage :

```bash
uv run streamlit run main.py
```

Le frontend est alors accessible dans le navigateur.

---

# Docker Compose

Docker Compose orchestre les deux services.

Architecture :

```text
docker-compose.yml
        ↓
backend
frontend
```

---

# build

```yaml
build:
  context: .
  dockerfile: Dockerfile
  target: backend
```

Décomposition :

## context

```yaml
context: .
```

Racine du projet :

```text
projet-ml/
```

Docker peut accéder :

* backend ;
* frontend ;
* artifacts.

---

## dockerfile

```yaml
dockerfile: Dockerfile
```

Indique le fichier Dockerfile à utiliser.

---

## target

```yaml
target: backend
```

Construit uniquement :

```text
FROM base AS backend
```

Le stage frontend est ignoré.

---

# Image Backend

```yaml
image: mon_image_backend_avancee:1.0
```

Nom de l'image générée.

---

# Volume

```yaml
volumes:
  - ./artifacts:/app/artifacts
```

Correspondance :

```text
Machine locale
└── artifacts
       ↓
Container
└── /app/artifacts
```

Avantages :

* modifier le modèle sans reconstruire l'image ;
* remplacer facilement un modèle ;
* faciliter les expérimentations ML.

---

# Variables d'environnement Backend

```yaml
environment:
  UVICORN_HOST: 0.0.0.0
  UVICORN_PORT: 8000
```

Le backend écoute sur :

```text
0.0.0.0:8000
```

---

# Service Frontend

```yaml
target: frontend
```

Construit uniquement :

```text
FROM base AS frontend
```

---

# Publication du port

```yaml
ports:
  - "8501:8501"
```

Correspondance :

```text
Machine locale : 8501
Container      : 8501
```

Application disponible :

```text
http://localhost:8501
```

---

# API_URL

```yaml
API_URL: http://backend:8000
```

Le frontend appelle :

```text
backend:8000
```

via le réseau Docker.

---

# depends_on

```yaml
depends_on:
  - backend
```

Ordre de démarrage :

```text
backend
     ↓
frontend
```

---

# Architecture finale

```text
Navigateur
      │
      │ localhost:8501
      ▼
Frontend (Streamlit)
      │
      │ http://backend:8000
      ▼
Backend (FastAPI)
      │
      │ charge
      ▼
flight_price_model.joblib
```

---

# Commandes principales

Construire et démarrer :

```bash
docker compose up
```

En arrière-plan :

```bash
docker compose up -d
```

Reconstruire les images :

```bash
docker compose up -d --build
```

Voir les services :

```bash
docker compose ps
```

Voir les logs :

```bash
docker compose logs -f
```

Voir les logs du backend :

```bash
docker compose logs backend
```

Voir les logs du frontend :

```bash
docker compose logs frontend
```

Entrer dans le backend :

```bash
docker compose exec backend bash
```

Entrer dans le frontend :

```bash
docker compose exec frontend bash
```

Arrêter :

```bash
docker compose stop
```

Supprimer les containers :

```bash
docker compose down
```

Voir la configuration finale :

```bash
docker compose config
```

---

# Résumé

```text
Dockerfile unique
        ↓
Stage base
        ↓
 ┌───────────────┐
 │               │
 ▼               ▼
Backend      Frontend
 │               │
 │               │
Modèle ML     Interface Web
 │               │
 └───────API─────┘
        ↓
 Navigateur
```

Le multi-stage permet :

* d'éviter la duplication de code ;
* de partager une base commune ;
* de profiter du cache Docker ;
* de construire des images plus propres ;
* de simplifier la maintenance des projets de Machine Learning.


# Augmenter la fiabilité avec un Healthcheck

Dans un projet de Machine Learning, le backend doit souvent :

1. démarrer FastAPI ;
2. charger le modèle de Machine Learning ;
3. initialiser certaines ressources ;
4. devenir réellement prêt à répondre aux requêtes.

Le chargement d'un modèle peut prendre plusieurs secondes, voire plusieurs dizaines de secondes.

---

# Le problème

Lorsque nous exécutons :

```bash id="tw5zha"
docker compose up
```

Docker démarre les containers.

Sans vérification supplémentaire :

```text id="p1fydm"
Backend démarre
        ↓
Frontend démarre immédiatement
        ↓
Le modèle ML n'est pas encore chargé
        ↓
Erreurs de connexion
```

Exemples :

* API indisponible ;
* erreurs HTTP ;
* page Streamlit incomplète ;
* échec des premières prédictions.

---

# Pourquoi cela arrive ?

Le container backend est démarré, mais cela ne signifie pas qu'il est prêt.

Exemple :

```text id="ev8smb"
Container démarré
        ≠
Application prête
```

Le backend peut encore être en train de :

```text id="3wdkn4"
Chargement de Python
        ↓
Chargement des dépendances
        ↓
Chargement du modèle .joblib
        ↓
Initialisation de FastAPI
        ↓
API prête
```

---

# La solution : le Healthcheck

Le Healthcheck est un bilan de santé du container.

Docker demande régulièrement :

```text id="ns03cc"
L'application est-elle réellement prête ?
```

Le frontend ne sera lancé que lorsque la réponse sera :

```text id="3hn18j"
Healthy
```

---

# Configuration

```yaml id="iv5gg1"
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 5s
  timeout: 3s
  retries: 3
  start_period: 5s
```

---

# test

```yaml id="p8crsv"
test:
  ["CMD", "curl", "-f", "http://localhost:8000/health"]
```

Docker exécute :

```bash id="d3f4dh"
curl -f http://localhost:8000/health
```

L'objectif est de vérifier que l'API répond correctement.

Exemple :

```text id="lxup0h"
GET /health
      ↓
200 OK
```

Le backend est alors considéré comme prêt.

---

# Pourquoi créer une route `/health` ?

Une route dédiée permet de vérifier :

* que FastAPI est démarré ;
* que le modèle est chargé ;
* que l'application peut accepter des requêtes.

Exemple :

```text id="v2zsjw"
Backend
      ↓
Modèle ML chargé
      ↓
/health → 200 OK
```

---

# interval

```yaml id="dx54q4"
interval: 5s
```

Docker exécute le test toutes les :

```text id="ap5p4g"
5 secondes
```

---

# timeout

```yaml id="pq8vg8"
timeout: 3s
```

Chaque test dispose de :

```text id="n0tk5y"
3 secondes
```

pour répondre.

---

# retries

```yaml id="e2kzng"
retries: 3
```

Docker tolère :

```text id="wnsddz"
3 échecs consécutifs
```

avant de considérer le service comme indisponible.

---

# start_period

```yaml id="i8xj72"
start_period: 5s
```

Docker accorde :

```text id="73jwmu"
5 secondes de démarrage
```

avant de commencer à compter les échecs.

Cette option est particulièrement utile pour les applications de Machine Learning qui nécessitent un temps d'initialisation.

---

# États possibles

```text id="n9ib71"
Starting
     ↓
Healthy
```

ou :

```text id="1j9knl"
Starting
     ↓
Unhealthy
```

---

# depends_on avec condition

```yaml id="7o4br8"
depends_on:
  backend:
    condition: service_healthy
```

Le frontend ne démarre plus immédiatement.

Nouveau comportement :

```text id="n4f6mb"
Backend démarre
       ↓
Chargement du modèle ML
       ↓
Healthcheck
       ↓
Healthy
       ↓
Frontend démarre
```

---

# Nouveau démarrage de l'application

Avant :

```text id="wq4k3d"
Backend
Frontend
      ↓
Erreurs possibles
```

Après :

```text id="f4m14f"
Backend
      ↓
Chargement du modèle
      ↓
Healthy
      ↓
Frontend
```

Le risque d'erreurs au démarrage est fortement réduit.

---

# Architecture finale

```text id="3f8af3"
docker compose up
        ↓
Backend démarre
        ↓
Chargement du modèle ML
        ↓
GET /health
        ↓
200 OK
        ↓
Healthy
        ↓
Frontend démarre
        ↓
Application disponible
```

---

# Vérifier l'état des services

Voir les containers :

```bash id="hcgylm"
docker compose ps
```

Exemple :

```text id="8z5sv7"
backend    running (healthy)
frontend   running
```

---

# Voir les logs du backend

```bash id="xv5yfr"
docker compose logs backend
```

Suivre les logs en temps réel :

```bash id="4nnj5z"
docker compose logs -f backend
```

---

# Tester manuellement le Healthcheck

Depuis la machine locale :

```bash id="f11nhh"
curl http://localhost:8000/health
```

Depuis le container backend :

```bash id="8gx4ij"
docker compose exec backend bash
curl http://localhost:8000/health
```

---

# Résumé

```text id="5agll8"
docker compose up
        ↓
Backend démarre
        ↓
Chargement du modèle ML
        ↓
Healthcheck
        ↓
Healthy
        ↓
Frontend démarre
        ↓
Application prête
```

Le Healthcheck permet :

* d'attendre que le modèle soit réellement chargé ;
* de réduire les erreurs de démarrage ;
* d'améliorer la fiabilité de l'application ;
* de garantir que le frontend appelle une API déjà opérationnelle.


# Monitoring : analyser la taille des images avec `docker history`

Lorsque l'on travaille sur des projets de Machine Learning, les images Docker peuvent rapidement devenir volumineuses :

* dépendances Python nombreuses ;
* bibliothèques de Machine Learning ;
* modèles `.joblib`, `.pkl` ou `.onnx` ;
* fichiers temporaires ;
* caches inutiles.

Il est donc important de comprendre **ce qui occupe de l'espace dans une image Docker**.

---

# La commande `docker history`

```bash id="6i8v2l"
docker history <nom_image>
```

Exemple :

```bash id="1vm4f8"
docker history mon_image_backend_avancee:1.0
```

Cette commande affiche :

* les différentes couches de l'image ;
* les commandes qui ont créé chaque couche ;
* la taille de chaque couche.

---

# Exemple de sortie

```text id="d4hm4x"
IMAGE          CREATED BY                     SIZE
<image_id>     CMD [...]                      0B
<image_id>     COPY backend/ .               10MB
<image_id>     RUN uv sync ...              350MB
<image_id>     COPY artifacts/...            80MB
<image_id>     RUN apt-get install ...       20MB
<image_id>     FROM debian:bookworm-slim     80MB
```

Chaque ligne représente une couche Docker.

---

# Pourquoi cette commande est-elle utile ?

Elle permet de répondre à des questions comme :

```text id="4p6twi"
Pourquoi mon image fait-elle 800 MB ?
```

ou :

```text id="h0i6fw"
Le modèle ML prend-il beaucoup de place ?
```

ou encore :

```text id="8xezbn"
Mes dépendances Python sont-elles trop lourdes ?
```

---

# Comprendre les couches Docker

Chaque instruction importante du Dockerfile crée généralement une nouvelle couche.

Exemple :

```dockerfile id="dcfdwp"
FROM debian:bookworm-slim
RUN apt-get install ...
COPY artifacts/flight_price_model.joblib ...
RUN uv sync ...
COPY backend/ .
```

devient :

```text id="r2lny7"
Couche Debian
      ↓
Couche apt-get
      ↓
Couche modèle ML
      ↓
Couche dépendances Python
      ↓
Couche code backend
```

---

# Cas d'un projet de Machine Learning

```text id="zwr5jp"
Image Backend
├── Debian                  80 MB
├── Dépendances Python     350 MB
├── Modèle ML               80 MB
└── Code applicatif          5 MB
```

On constate souvent que :

* les dépendances Python sont les plus lourdes ;
* les modèles de Machine Learning peuvent également prendre beaucoup de place ;
* le code Python lui-même est généralement très léger.

---

# Détecter les optimisations possibles

Exemple :

```text id="vzkdfw"
RUN apt-get install ...      150 MB
```

Cela peut indiquer :

* trop de paquets installés ;
* cache non supprimé ;
* outils inutiles en production.

---

Exemple :

```text id="p5vhhq"
COPY artifacts/...           800 MB
```

Cela peut indiquer :

* un modèle trop volumineux ;
* plusieurs modèles copiés inutilement ;
* des artefacts qui devraient être montés via un volume.

---

# Exemple d'optimisation

Avant :

```dockerfile id="0h1o0f"
RUN apt-get update && apt-get install -y ca-certificates
```

Après :

```dockerfile id="wlxv4q"
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*
```

Résultat :

```text id="q9t68g"
Image plus légère
```

---

# Vérifier plusieurs images

Backend :

```bash id="m2q4m6"
docker history mon_image_backend_avancee:1.0
```

Frontend :

```bash id="dfe37v"
docker history mon_image_frontend_avancee:1.0
```

Comparer les deux images permet de comprendre :

```text id="h0z7u0"
Quelle image est la plus lourde ?
Quelles couches occupent le plus d'espace ?
```

---

# Voir uniquement la taille totale

```bash id="l9q6iz"
docker images
```

Exemple :

```text id="3y8r4m"
REPOSITORY                     SIZE
mon_image_backend_avancee      620MB
mon_image_frontend_avancee     280MB
```

Puis :

```bash id="k6v9mw"
docker history mon_image_backend_avancee:1.0
```

pour comprendre d'où proviennent ces 620 MB.

---

# Résumé

```text id="8n6mxy"
docker images
       ↓
Voir la taille totale
       ↓
docker history
       ↓
Voir le détail de chaque couche
       ↓
Identifier les couches lourdes
       ↓
Optimiser le Dockerfile
```

La commande :

```bash id="o5x9wt"
docker history <nom_image>
```

est un excellent outil de monitoring pour :

* comprendre la composition d'une image ;
* identifier les couches les plus volumineuses ;
* optimiser les images Docker ;
* réduire le temps de téléchargement et de déploiement ;
* améliorer les performances des projets de Machine Learning.



# Developer Experience (DX) avec Docker

L'objectif de la **Developer Experience (DX)** est de :

* développer plus rapidement ;
* réduire les temps d'attente ;
* travailler dans un environnement identique pour toute l'équipe ;
* éviter de reconstruire les images à chaque modification.

---

# 1. Hot Reload

## Le problème

Pendant le développement, nous modifions souvent le code :

```text id="rxvktv"
Modifier un fichier
      ↓
docker compose up --build
      ↓
Reconstruction de l'image
      ↓
Redémarrage des containers
```

Cette approche devient rapidement lente et peu productive.

---

# La solution : le Hot Reload

Le Hot Reload permet :

```text id="39uzg8"
Modifier un fichier
      ↓
Sauvegarder
      ↓
Application redémarrée automatiquement
```

Aucune reconstruction de l'image n'est nécessaire.

---

# Volume du Backend

```yaml id="f33g2f"
volumes:
  - ./backend:/app
```

Correspondance :

```text id="r3ydfx"
Machine locale
└── backend/
       ↓
Container
└── /app
```

Toute modification dans :

```text id="z5o7oz"
backend/
```

est immédiatement visible dans le container.

---

# Volume du Frontend

```yaml id="g1xq0n"
volumes:
  - ./frontend:/app
```

Correspondance :

```text id="1wh1sa"
Machine locale
└── frontend/
       ↓
Container
└── /app
```

Les modifications sont instantanément disponibles dans Streamlit.

---

# Préserver l'environnement Python

```yaml id="m6es74"
- /app/.venv
```

Ce volume anonyme permet de conserver :

```text id="xvbh5z"
/app/.venv
```

Pourquoi ?

Sans cela :

```text id="ckc0t1"
./backend:/app
```

écraserait complètement :

```text id="e9vtm8"
/app
└── .venv
```

et les dépendances Python disparaîtraient.

---

# Rechargement automatique du Backend

```yaml id="s2ksiz"
environment:
  UVICORN_RELOAD: true
```

Uvicorn surveille les fichiers :

```text id="v50xov"
Modifier un fichier Python
      ↓
Détection automatique
      ↓
Redémarrage du serveur
```

Aucune commande supplémentaire n'est nécessaire.

---

# Rechargement automatique du Frontend

Streamlit possède déjà son propre système de Hot Reload.

```text id="3hslpz"
Modifier main.py
      ↓
Sauvegarder
      ↓
Page Streamlit actualisée automatiquement
```

---

# Nouveau workflow de développement

Avant :

```text id="zbg8ci"
Modifier le code
      ↓
docker compose up --build
      ↓
Attendre
```

Après :

```text id="k56dc0"
Modifier le code
      ↓
Sauvegarder
      ↓
Application mise à jour immédiatement
```

---

# 2. Dev Containers

## Le problème

Chaque développeur possède une machine différente :

```text id="xg7a5w"
Python 3.11
Python 3.12
Windows
Linux
Mac
```

Des problèmes de compatibilité apparaissent rapidement.

---

# La solution : Dev Containers

Les Dev Containers permettent d'ouvrir directement VSCode dans le container Docker.

Architecture :

```text id="6vmxke"
VSCode
    ↓
Container Docker
    ↓
Python + Dépendances
```

Le code est développé directement dans le container.

---

# Structure

```text id="0mn9cl"
.devcontainer/
├── backend/
│   └── devcontainer.json
└── frontend/
    └── devcontainer.json
```

---

# dockerComposeFile

```json id="q4b4y6"
"dockerComposeFile": "../../docker-compose.yml"
```

VSCode utilise directement :

```text id="vpx99n"
docker-compose.yml
```

Les mêmes containers sont utilisés pour le développement.

---

# service

Backend :

```json id="c7umig"
"service": "backend"
```

Frontend :

```json id="kznvze"
"service": "frontend"
```

VSCode se connecte directement au service choisi.

---

# workspaceFolder

```json id="lj1pzw"
"workspaceFolder": "/app"
```

Le dossier de travail de VSCode devient :

```text id="ot0x1k"
/app
```

C'est le dossier contenant le projet dans le container.

---

# Python Interpreter

```json id="fsl3l4"
"python.defaultInterpreterPath":
"/app/.venv/bin/python"
```

VSCode utilise automatiquement :

```text id="yjvwaw"
/app/.venv/bin/python
```

Toutes les dépendances installées par `uv` sont immédiatement disponibles.

---

# Extensions VSCode

```json id="w0q75g"
"extensions": [
  "ms-python.python"
]
```

Installe automatiquement :

* coloration syntaxique ;
* autocomplétion ;
* débogage Python ;
* exécution de scripts.

---

# remoteUser

```json id="8cslj4"
"remoteUser": "root"
```

VSCode ouvre le container en tant que :

```text id="pmd7g9"
root
```

et possède tous les droits nécessaires.

---

# Workflow avec Dev Containers

```text id="uw4e7r"
docker compose up
       ↓
Ouvrir VSCode
       ↓
Reopen in Container
       ↓
Développement directement dans Docker
```

---

# Commandes utiles

Construire et démarrer :

```bash id="twh76j"
docker compose up -d
```

Voir les logs :

```bash id="eyjlwm"
docker compose logs -f
```

Entrer dans le backend :

```bash id="pvn3ur"
docker compose exec backend bash
```

Entrer dans le frontend :

```bash id="y6j7z2"
docker compose exec frontend bash
```

---

# 3. Sujets avancés : les images `<none>`

Après plusieurs :

```bash id="l3xij6"
docker compose up --build
```

on observe parfois :

```bash id="6v54yw"
docker images
```

Exemple :

```text id="ozhq8m"
REPOSITORY                 TAG       IMAGE ID
<none>                     <none>    abc123
<none>                     <none>    def456
mon_image_backend_avancee  1.0       xyz789
```

---

# Pourquoi ces images apparaissent-elles ?

À chaque reconstruction :

```text id="2w6q3x"
Ancienne image
      ↓
Nouvelle image
```

Docker conserve parfois l'ancienne image.

Comme elle n'a plus de nom :

```text id="1u4l2r"
<none>:<none>
```

on parle d'images **dangling**.

---

# Faut-il les supprimer ?

Elles ne sont pas dangereuses.

Mais elles :

* occupent de l'espace disque ;
* s'accumulent avec le temps ;
* peuvent représenter plusieurs Go dans des projets ML.

---

# Voir les images inutilisées

```bash id="zwgksq"
docker image ls -f dangling=true
```

---

# Supprimer les images inutilisées

```bash id="2w3llg"
docker image prune
```

Docker demande une confirmation :

```text id="ph79r8"
Delete all dangling images ?
```

Répondre :

```text id="eg6o83"
y
```

---

# Supprimer sans confirmation

```bash id="f7z2p3"
docker image prune -f
```

---

# Nettoyage plus complet

```bash id="aavk8v"
docker system prune
```

Supprime :

* containers arrêtés ;
* réseaux inutilisés ;
* images dangling ;
* cache de build.

---

# Nettoyage complet avec volumes

```bash id="6wx7ry"
docker system prune -a --volumes
```

⚠️ Cette commande peut supprimer plusieurs Go de données et supprimer des ressources encore utiles.

---

# Vérifier l'espace utilisé

```bash id="kryy7w"
docker system df
```

Exemple :

```text id="ks40p4"
Images      5.2GB
Containers  200MB
Volumes     1.4GB
Build Cache 800MB
```

Cette commande est particulièrement utile dans les projets de Machine Learning où :

* les images sont volumineuses ;
* les modèles sont lourds ;
* les reconstructions sont fréquentes.

---

# Résumé

```text id="kkzzwa"
Volumes + Hot Reload
        ↓
Développement instantané
        ↓
Dev Containers
        ↓
Environnement identique pour tous
        ↓
docker compose up --build
        ↓
Accumulation d'images <none>
        ↓
docker image prune
        ↓
Nettoyage de Docker
```

La combinaison :

```text id="rnrr1w"
Hot Reload
+ Dev Containers
+ Nettoyage régulier de Docker
```

permet d'obtenir une excellente expérience de développement, même sur des projets de Machine Learning plus volumineux.
