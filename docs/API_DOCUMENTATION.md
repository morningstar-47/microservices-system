# API Documentation - Microservices Auth

## Vue d'ensemble

Cette architecture microservices fournit une solution complète pour la gestion de l'authentification et des utilisateurs.

### Services

1. **API Gateway** (Port 8080) - Point d'entrée unique
2. **Auth Service** (Port 8001) - Gestion de l'authentification
3. **User Service** (Port 8002) - Gestion des utilisateurs

## Authentification

L'API utilise JWT (JSON Web Tokens) pour l'authentification. Les tokens doivent être inclus dans l'en-tête `Authorization` avec le format : `Bearer <token>`

## Endpoints

### Auth Service (via API Gateway)

#### POST /auth/register
Enregistre un nouvel utilisateur.

**Request Body:**
```json
{
  "username": "string",
  "email": "user@example.com",
  "password": "string",
  "full_name": "string" (optional)
}
```

**Response (201):**
```json
{
  "message": "User registered successfully",
  "user_id": 1
}
```

**Validation Rules:**
- Username: minimum 3 caractères, alphanumérique avec _ et -
- Password: minimum 8 caractères, au moins 1 majuscule et 1 chiffre
- Email: format email valide

#### POST /auth/login
Authentifie un utilisateur et retourne un token JWT.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200):**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### GET /auth/verify
Vérifie la validité d'un token JWT.

**Headers:**
- `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "username": "string",
  "valid": true
}
```

### User Service (via API Gateway)

#### POST /users
Crée un nouvel utilisateur (nécessite authentification).

**Headers:**
- `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "username": "string",
  "email": "user@example.com",
  "full_name": "string" (optional),
  "role": "user" | "admin" (default: "user")
}
```

**Response (201):**
```json
{
  "id": "string",
  "username": "string",
  "email": "user@example.com",
  "full_name": "string",
  "created_by": "string",
  "created_at": "2024-01-01T00:00:00",
  "is_active": true,
  "role": "user"
}
```

#### GET /users
Récupère la liste des utilisateurs (nécessite authentification).

**Headers:**
- `Authorization: Bearer <token>`

**Query Parameters:**
- `skip`: nombre d'enregistrements à ignorer (default: 0)
- `limit`: nombre maximum d'enregistrements à retourner (default: 100)
- `is_active`: filtrer par statut actif (optional)

**Response (200):**
```json
[
  {
    "id": "string",
    "username": "string",
    "email": "user@example.com",
    "full_name": "string",
    "created_by": "string",
    "created_at": "2024-01-01T00:00:00",
    "is_active": true,
    "role": "user"
  }
]
```

#### GET /users/{user_id}
Récupère les détails d'un utilisateur spécifique.

**Headers:**
- `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": "string",
  "username": "string",
  "email": "user@example.com",
  "full_name": "string",
  "created_by": "string",
  "created_at": "2024-01-01T00:00:00",
  "is_active": true,
  "role": "user"
}
```

#### PATCH /users/{user_id}
Met à jour un utilisateur.

**Headers:**
- `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "email": "newemail@example.com" (optional),
  "full_name": "New Name" (optional),
  "is_active": false (optional)
}
```

**Response (200):** Utilisateur mis à jour

#### DELETE /users/{user_id}
Supprime (désactive) un utilisateur.

**Headers:**
- `Authorization: Bearer <token>`

**Response (204):** No Content

### Health Check

#### GET /health
Vérifie l'état de santé du service.

**Response (200):**
```json
{
  "status": "healthy",
  "service": "api-gateway",
  "timestamp": "2024-01-01T00:00:00",
  "services": {
    "auth-service": true,
    "user-service": true
  }
}
```

## Codes d'erreur

| Code | Description |
|------|-------------|
| 400 | Bad Request - Données invalides |
| 401 | Unauthorized - Token manquant ou invalide |
| 403 | Forbidden - Accès refusé |
| 404 | Not Found - Ressource non trouvée |
| 409 | Conflict - Conflit (ex: utilisateur existe déjà) |
| 422 | Unprocessable Entity - Erreur de validation |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

## Exemples d'utilisation

### Inscription et connexion

```bash
# Inscription
curl -X POST http://localhost:8080/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'

# Connexion
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "SecurePass123!"
  }'

# Récupérer le token de la réponse et l'utiliser pour les requêtes suivantes
```

### Gestion des utilisateurs

```bash
# Créer un utilisateur
curl -X POST http://localhost:8080/users \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "full_name": "New User"
  }'

# Lister les utilisateurs
curl -X GET http://localhost:8080/users \
  -H "Authorization: Bearer <your-token>"

# Obtenir un utilisateur spécifique
curl -X GET http://localhost:8080/users/<user-id> \
  -H "Authorization: Bearer <your-token>"
```

## Rate Limiting

En production, l'API Gateway implémente un rate limiting :
- 100 requêtes par minute pour les endpoints non authentifiés
- 1000 requêtes par minute pour les endpoints authentifiés

## Monitoring

Les métriques sont disponibles via Prometheus sur :
- http://localhost:9090 - Prometheus
- http://localhost:3000 - Grafana (admin/admin)

## SDK Python

```python
import httpx
from typing import Optional, Dict, List

class MicroservicesAuthClient:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.client = httpx.Client()
    
    def register(self, username: str, email: str, password: str, full_name: Optional[str] = None) -> Dict:
        response = self.client.post(
            f"{self.base_url}/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password,
                "full_name": full_name
            }
        )
        response.raise_for_status()
        return response.json()
    
    def login(self, username: str, password: str) -> Dict:
        response = self.client.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        data = response.json()
        self.token = data["access_token"]
        return data
    
    def get_users(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        if not self.token:
            raise ValueError("Not authenticated. Please login first.")
        
        response = self.client.get(
            f"{self.base_url}/users",
            headers={"Authorization": f"Bearer {self.token}"},
            params={"skip": skip, "limit": limit}
        )
        response.raise_for_status()
        return response.json()
```