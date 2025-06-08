#!/bin/bash

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Checking Microservices Status ===${NC}\n"

# Check Docker containers
echo -e "${YELLOW}Docker Containers:${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo -e "\n${YELLOW}Database Connectivity:${NC}"

# Check PostgreSQL
echo -n "PostgreSQL: "
if docker-compose exec -T postgres pg_isready -U user -d auth_db > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Connected${NC}"
    # Try to connect and show tables
    docker-compose exec -T postgres psql -U user -d auth_db -c "\dt" 2>/dev/null || echo "  (No tables yet)"
else
    echo -e "${RED}✗ Not reachable${NC}"
    echo "  Logs:"
    docker-compose logs --tail=10 postgres
fi

# Check MongoDB
echo -n "MongoDB: "
if docker-compose exec -T mongo mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Connected${NC}"
    # Show collections
    docker-compose exec -T mongo mongosh user_db --eval "db.getCollectionNames()" 2>/dev/null || echo "  (No collections yet)"
else
    echo -e "${RED}✗ Not reachable${NC}"
    echo "  Logs:"
    docker-compose logs --tail=10 mongo
fi

# Check Redis
echo -n "Redis: "
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Connected${NC}"
else
    echo -e "${RED}✗ Not reachable${NC}"
    echo "  Logs:"
    docker-compose logs --tail=10 redis
fi

echo -e "\n${YELLOW}Service Health Endpoints:${NC}"

# Check services health endpoints
for service in "api-gateway:8080" "auth-service:8001" "user-service:8002"; do
    IFS=':' read -r name port <<< "$service"
    echo -n "$name (port $port): "
    
    if curl -s -f "http://localhost:$port/health" > /dev/null 2>&1; then
        health=$(curl -s "http://localhost:$port/health" | jq -r '.status // "unknown"' 2>/dev/null || echo "unknown")
        echo -e "${GREEN}✓ Healthy${NC} (status: $health)"
    else
        echo -e "${RED}✗ Not responding${NC}"
        # Check if container is running
        if docker ps | grep -q "$name"; then
            echo "  Container is running. Recent logs:"
            docker-compose logs --tail=5 "$name" 2>&1 | sed 's/^/  /'
        else
            echo "  Container is not running"
        fi
    fi
done

echo -e "\n${YELLOW}Network Connectivity:${NC}"
# Check network
network_name="microservices-system_microservices-network"
echo -n "Docker network: "
if docker network ls | grep -q "$network_name"; then
    echo -e "${GREEN}✓ Exists${NC}"
    # Show connected containers
    echo "  Connected containers:"
    docker network inspect "$network_name" -f '{{range .Containers}}  - {{.Name}}{{"\n"}}{{end}}' 2>/dev/null || echo "  Unable to inspect"
else
    echo -e "${RED}✗ Not found${NC}"
fi

echo -e "\n${YELLOW}Port Availability:${NC}"
for port in 8080 8001 8002 8003 8004 8005 5432 27017 6379; do
    echo -n "Port $port: "
    if lsof -i :$port > /dev/null 2>&1; then
        echo -e "${GREEN}✓ In use${NC}"
    else
        echo -e "${RED}✗ Not in use${NC}"
    fi
done

echo -e "\n${YELLOW}Environment Check:${NC}"
if [ -f .env ]; then
    echo -e "${GREEN}✓ .env file exists${NC}"
    echo "  JWT_SECRET is $(grep JWT_SECRET .env > /dev/null && echo 'set' || echo 'not set')"
else
    echo -e "${RED}✗ .env file missing${NC}"
fi

echo -e "\n${GREEN}=== Check Complete ===${NC}"