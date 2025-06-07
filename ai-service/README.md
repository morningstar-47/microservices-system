# AI Service

Ce service est responsable de l'intégration et de la gestion des fonctionnalités d'intelligence artificielle dans le système de microservices.

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
AI_MODEL_PATH=/path/to/model
AI_API_KEY=your_api_key
LOG_LEVEL=INFO
```

Adaptez les valeurs selon vos besoins.

## Documentation

Retrouvez la documentation détaillée du service dans le répertoire `docs/` :

*   [Documentation API](./docs/API_DOCUMENTATION.md)
*   [Guide de dépannage](./docs/TROUBLESHOOTING.md)

## Structure du projet

```
ai-service/
├── docs/
│   ├── API_DOCUMENTATION.md
│   └── TROUBLESHOOTING.md
├── .env  (à créer)
└── README.md
```

## Prérequis

- Python 3.11
- Docker (optionnel, pour la base de données en local)

## Lancer les tests localement

Exécutez les commandes suivantes à la racine du service :

```bash
pip install -r requirements.txt
pytest
```

## Intégration continue (CI)

À chaque push ou pull request, tous les tests du service sont exécutés automatiquement via GitHub Actions.