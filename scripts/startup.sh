#!/bin/bash

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Microservices System Stack...${NC}"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Please update .env with your configuration${NC}"
fi

# Function to wait for a service
wait_for_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=1

    echo -e "Waiting for ${service}..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ ${service} is ready${NC}"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "\n${RED}✗ ${service} failed to start${NC}"
    return 1
}

# Function to wait for PostgreSQL
wait_for_postgres() {
    local max_attempts=30
    local attempt=1

    echo -e "Waiting for PostgreSQL..."
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose exec -T postgres pg_isready -U user -d auth_db > /dev/null 2>&1; then
            echo -e "${GREEN}✓ PostgreSQL is ready${NC}"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "\n${RED}✗ PostgreSQL failed to start${NC}"
    return 1
}

# Function to wait for MongoDB
wait_for_mongo() {
    local max_attempts=30
    local attempt=1

    echo -e "Waiting for MongoDB..."
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose exec -T mongo mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ MongoDB is ready${NC}"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "\n${RED}✗ MongoDB failed to start${NC}"
    return 1
}

# Function to wait for Redis
wait_for_redis() {
    local max_attempts=30
    local attempt=1

    echo -e "Waiting for Redis..."
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Redis is ready${NC}"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "\n${RED}✗ Redis failed to start${NC}"
    return 1
}

# Start databases first
echo -e "\n${GREEN}Starting databases...${NC}"
docker-compose up -d postgres mongo redis

# Wait for databases
wait_for_postgres || exit 1
wait_for_mongo || exit 1
wait_for_redis || exit 1

# Initialize databases if needed
echo -e "\n${GREEN}Initializing databases...${NC}"
sleep 5

# Check if auth_db tables exist
if ! docker-compose exec -T postgres psql -U user -d auth_db -c "SELECT 1 FROM users LIMIT 1;" > /dev/null 2>&1; then
    echo "Creating auth service tables..."
    docker-compose exec -T postgres psql -U user -d auth_db << EOF
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

INSERT INTO users (username, email, hashed_password, full_name, is_active) VALUES ('admin', 'admin@example.com', 'AdminPasswoord123', 'Admin User', TRUE);
EOF
    echo -e "${GREEN}✓ Auth database initialized${NC}"
fi

# Start services
echo -e "\n${GREEN}Starting microservices...${NC}"
docker-compose up -d auth-service user-service map-service ai-service report-service

# Wait for services
wait_for_service "Auth Service" "http://localhost:8001/health" || exit 1
wait_for_service "User Service" "http://localhost:8002/health" || exit 1
wait_for_service "Map Service" "http://localhost:8003/health" || exit 1
wait_for_service "AI Service" "http://localhost:8004/health" || exit 1
wait_for_service "Report Service" "http://localhost:8005/health" || exit 1

# Start API Gateway
echo -e "\n${GREEN}Starting API Gateway...${NC}"
docker-compose up -d api-gateway

wait_for_service "API Gateway" "http://localhost:8080/health" || exit 1

# Start monitoring (optional)
read -p "Start monitoring stack (Prometheus + Grafana)? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\n${GREEN}Starting monitoring stack...${NC}"
    docker-compose up -d prometheus grafana
    wait_for_service "Prometheus" "http://localhost:9090" || echo -e "${YELLOW}Prometheus startup failed${NC}"
    wait_for_service "Grafana" "http://localhost:3000" || echo -e "${YELLOW}Grafana startup failed${NC}"
fi

# Show status
echo -e "\n${GREEN}=== Microservices Status ===${NC}"
docker-compose ps

echo -e "\n${GREEN}=== Available Endpoints ===${NC}"
echo "API Gateway: http://localhost:8080"
echo "Auth Service: http://localhost:8001"
echo "User Service: http://localhost:8002"
echo "Map Service: http://localhost:8003"
echo "AI Service: http://localhost:8004"
echo "Report Service: http://localhost:8005"
echo "PostgreSQL: http://localhost:5432"
echo "MongoDB: http://localhost:27017"
echo "Redis: http://localhost:6379"

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Prometheus: http://localhost:9090"
    echo "Grafana: http://localhost:3000 (admin/admin)"
fi

echo -e "\n${GREEN}Stack is ready!${NC}"
echo "Try: curl http://localhost:8080/health | jq"

# Follow logs
read -p "Follow logs? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose logs -f
fi