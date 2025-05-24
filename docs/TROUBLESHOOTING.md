# Guide de dépannage - Microservices Auth

## Problèmes courants et solutions

### 1. Service unhealthy

**Symptôme** : `dependency failed to start: container [service-name] is unhealthy`

**Solutions** :

```bash
# Vérifier les logs du service
docker-compose logs -f [service-name]

# Redémarrer le service spécifique
docker-compose restart [service-name]

# Reconstruire et redémarrer
docker-compose build [service-name]
docker-compose up -d [service-name]
```

### 2. Erreur de connexion à la base de données

**Auth Service - PostgreSQL**
```bash
# Vérifier que PostgreSQL est accessible
docker-compose exec postgres psql -U user -d auth_db -c "SELECT 1;"

# Recréer la base de données
docker-compose exec postgres psql -U user -c "DROP DATABASE IF EXISTS auth_db;"
docker-compose exec postgres psql -U user -c "CREATE DATABASE auth_db;"
```

**User Service - MongoDB**
```bash
# Vérifier que MongoDB est accessible
docker-compose exec mongo mongosh --eval "db.adminCommand('ping')"

# Vérifier la connexion
docker-compose exec mongo mongosh user_db --eval "db.stats()"
```

### 3. Redis security warning

**Symptôme** : `Possible SECURITY ATTACK detected`

**Solution** : C'est un avertissement normal quand d'autres services tentent de se connecter à Redis avec HTTP. Pour l'éviter :

```bash
# Configurer Redis avec un mot de passe
docker-compose exec redis redis-cli CONFIG SET requirepass "your-redis-password"
```

### 4. Services ne démarrent pas dans le bon ordre

**Solution** : Utiliser le script de démarrage intelligent

```bash
chmod +x scripts/startup.sh
./scripts/startup.sh
```

### 5. Erreur "Module not found"

**Solution** : Reconstruire les images avec --no-cache

```bash
docker-compose build --no-cache
docker-compose up -d
```

### 6. Port déjà utilisé

**Symptôme** : `bind: address already in use`

**Solution** :
```bash
# Identifier le processus utilisant le port
sudo lsof -i :8080  # Remplacer 8080 par le port concerné

# Tuer le processus
sudo kill -9 [PID]

# Ou changer les ports dans docker-compose.yml
```

### 7. Problèmes de performances

**Vérifier les ressources Docker** :
```bash
docker stats

# Augmenter les ressources Docker Desktop
# Settings > Resources > Augmenter CPU/Memory
```

### 8. Logs et debugging

**Commandes utiles** :

```bash
# Voir tous les logs
docker-compose logs -f

# Logs d'un service spécifique
docker-compose logs -f auth-service

# Exécuter des commandes dans un conteneur
docker-compose exec auth-service bash

# Vérifier les variables d'environnement
docker-compose exec auth-service env

# Test de santé manuel
curl http://localhost:8001/health | jq
```

### 9. Réinitialisation complète

Si rien ne fonctionne, réinitialiser tout :

```bash
# Arrêter et supprimer tout
docker-compose down -v

# Supprimer toutes les images
docker-compose rm -f

# Nettoyer le système Docker
docker system prune -a

# Reconstruire et redémarrer
docker-compose build --no-cache
docker-compose up -d
```

### 10. Vérification de l'état du système

Script de diagnostic :

```bash
#!/bin/bash
echo "=== Docker Status ==="
docker ps -a

echo -e "\n=== Network Status ==="
docker network ls
docker network inspect microservices-auth_microservices-network

echo -e "\n=== Volume Status ==="
docker volume ls

echo -e "\n=== Service Health ==="
for service in api-gateway auth-service user-service postgres mongo redis; do
    echo -n "$service: "
    docker-compose ps $service | grep -q "Up" && echo "✓ UP" || echo "✗ DOWN"
done

echo -e "\n=== Endpoints Test ==="
for endpoint in "8080" "8001" "8002"; do
    echo -n "localhost:$endpoint/health: "
    curl -s http://localhost:$endpoint/health > /dev/null && echo "✓ OK" || echo "✗ FAIL"
done
```

## Monitoring et métriques

### Vérifier Prometheus
```bash
# Targets actifs
curl http://localhost:9090/api/v1/targets | jq

# Métriques disponibles
curl http://localhost:9090/api/v1/label/__name__/values | jq
```

### Accéder à Grafana
- URL : http://localhost:3000
- Login : admin / admin
- Ajouter data source : Prometheus (http://prometheus:9090)

## Support

Si vous rencontrez d'autres problèmes :

1. Vérifiez les logs détaillés
2. Assurez-vous que toutes les dépendances sont installées
3. Vérifiez la configuration dans `.env`
4. Consultez la documentation des services individuels