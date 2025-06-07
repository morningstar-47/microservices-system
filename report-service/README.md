# Report Service

Ce service est responsable de la génération et de la gestion des rapports dans le système de microservices.

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
REPORT_TEMPLATE_PATH=/path/to/templates
REPORT_OUTPUT_DIR=/path/to/output
LOG_LEVEL=INFO
```

Adaptez les valeurs selon vos besoins.

## Documentation

Retrouvez la documentation détaillée du service dans le répertoire `docs/` :

*   [Documentation API](./docs/API_DOCUMENTATION.md)
*   [Guide de dépannage](./docs/TROUBLESHOOTING.md)

## Structure du projet

```
report-service/
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