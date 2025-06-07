# Microservices System

Ce projet implémente une architecture de microservices pour la gestion de l'authentification, des utilisateurs, de l'intelligence artificielle, des rapports et des cartes.

Il comprend les services suivants :
- **api-gateway** : Point d'entrée unique pour les clients, gérant le routage et l'authentification.
- **auth-service** : Gère l'authentification des utilisateurs (inscription, connexion, etc.).
- **user-service** : Gère les informations des utilisateurs.
- **ai-service** : Gère les fonctionnalités d'intelligence artificielle.
- **report-service** : Gère la génération et la gestion des rapports.
- **map-service** : Gère l'affichage et la gestion des cartes.
- **postgres** : Base de données PostgreSQL pour le auth-service.
- **mongo** : Base de données MongoDB pour le user-service, ai-service, report-service et map-service.
- **redis** : Cache Redis (pour usage futur).
- **prometheus** : Outil de monitoring.
- **grafana** : Tableau de bord de monitoring.

## Démarrage rapide avec Docker Compose

Assurez-vous d'avoir Docker et Docker Compose installés.

1. Clonez ce dépôt.
2. Naviguez dans le répertoire `microservices-system`.
3. Créez un fichier `.env` à la racine du répertoire `microservices-system` si vous ne l'avez pas déjà fait (voir la section Configuration).
4. Lancez les services :

```bash
docker compose up --build -d
```

Cela construira les images Docker si nécessaire et démarrera tous les services en arrière-plan.

Pour arrêter les services :

```bash
docker compose down
```

## Configuration

Un fichier `.env` est nécessaire à la racine du répertoire `microservices-system` pour définir les variables d'environnement. Voici un exemple de contenu :

```env
DB_USER=user
DB_PASSWORD=password
DB_NAME=auth_db
JWT_SECRET=changeme
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30
ENVIRONMENT=development
LOG_LEVEL=INFO
CORS_ORIGINS=*
REQUEST_TIMEOUT=30
MONGO_DB_NAME=user_db
GRAFANA_PASSWORD=admin
AI_MODEL_PATH=/path/to/model
AI_API_KEY=your_api_key
REPORT_TEMPLATE_PATH=/path/to/templates
REPORT_OUTPUT_DIR=/path/to/output
MAP_API_KEY=your_map_api_key
MAP_CENTER_LAT=48.8566
MAP_CENTER_LNG=2.3522
```

Adaptez les valeurs selon vos besoins, en particulier `JWT_SECRET` pour la production.

## Documentation

Retrouvez la documentation détaillée du projet dans le répertoire `docs/` :

*   [Documentation API](./docs/API_DOCUMENTATION.md)
*   [Guide de dépannage](./docs/TROUBLESHOOTING.md)

## CI/CD

Ce projet utilise GitHub Actions pour l'intégration continue. Le workflow est défini dans `.github/workflows/ci.yml` et permet de vérifier la construction et le démarrage des services Docker à chaque push et pull request.

## Structure du projet

```
microservices-system/
├── api-gateway/
├── auth-service/
├── ai-service/
├── report-service/
├── map-service/
├── docs/
│   ├── API_DOCUMENTATION.md
│   └── TROUBLESHOOTING.md
├── init-scripts/
├── monitoring/
├── user-service/
├── .env  (à créer)
├── .github/
│   └── workflows/
│       └── ci.yml
└── docker-compose.yml
└── README.md
```

```mermaid
graph TD
    Client -->|HTTP| API-Gateway
    API-Gateway --> Auth-Service
    API-Gateway --> User-Service
    API-Gateway --> AI-Service
    API-Gateway --> Report-Service
    API-Gateway --> Map-Service
```

## Prérequis

- Python 3.11
- Docker (optionnel, pour la base de données en local)
- PostgreSQL (pour Auth-Service)
- MongoDB (pour User-Service, AI-Service, Report-Service et Map-Service)

## Lancer les tests localement

Chaque service possède ses propres dépendances et tests.  
Exécutez les commandes suivantes à la racine du projet :

### Auth-Service

```bash
cd auth-service
pip install -r requirements.txt
pytest
```

### User-Service

```bash
cd user-service
pip install -r requirements.txt
pytest
```

### API-Gateway

```bash
cd api-gateway
pip install -r requirements.txt
pytest
```

### AI-Service

```bash
cd ai-service
pip install -r requirements.txt
pytest
```

### Report-Service

```bash
cd report-service
pip install -r requirements.txt
pytest
```

### Map-Service

```bash
cd map-service
pip install -r requirements.txt
pytest
```

## Intégration continue (CI)

À chaque push ou pull request, tous les tests de chaque service sont exécutés automatiquement via GitHub Actions.  
Le workflow se trouve dans `.github/workflows/ci.yml`.