#!/bin/bash
# Test script for å sjekke at alle tjenester kjører riktig

echo "🔍 SJEKKER SHOPIFY ROYALTIES DASHBOARD TJENESTER"
echo "================================================"

# Farger for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_service() {
    local service=$1
    local port=$2
    local name=$3
    
    if netstat -tlnp 2>/dev/null | grep ":$port" > /dev/null; then
        echo -e "${GREEN}✅ $name kjører på port $port${NC}"
        return 0
    else
        echo -e "${RED}❌ $name kjører IKKE på port $port${NC}"
        return 1
    fi
}

check_docker_container() {
    local container=$1
    local name=$2
    
    if docker ps | grep "$container" > /dev/null; then
        echo -e "${GREEN}✅ $name container kjører${NC}"
        return 0
    else
        echo -e "${RED}❌ $name container kjører IKKE${NC}"
        return 1
    fi
}

# Sjekk grunnleggende tjenester
echo -e "${YELLOW}📊 Grunnleggende tjenester:${NC}"
check_service "5433" "5433" "PostgreSQL Database"
check_service "5050" "5050" "pgAdmin"
check_service "8080" "8080" "Dashboard Webserver"

echo ""

# Sjekk Docker containers
echo -e "${YELLOW}🐳 Docker containers:${NC}"
check_docker_container "pgadmin" "pgAdmin"

echo ""

# Sjekk cronjobs
echo -e "${YELLOW}⏰ Cronjobs:${NC}"
if crontab -l | grep -E "(shopify|royalties)" > /dev/null; then
    echo -e "${GREEN}✅ Shopify cronjobs er konfigurert${NC}"
else
    echo -e "${RED}❌ Shopify cronjobs mangler${NC}"
fi

echo ""

# Sjekk database-tilkobling
echo -e "${YELLOW}🗄️ Database-tilkobling:${NC}"
if pg_isready -h localhost -p 5433 -U shopifyuser > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL database tilgjengelig${NC}"
    
    # Sjekk tabeller
    TABLE_COUNT=$(psql postgresql://shopifyuser:${POSTGRES_PASSWORD:-your-secure-database-password}@localhost:5433/shopify -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')
    if [ "$TABLE_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✅ Database har $TABLE_COUNT tabeller${NC}"
    else
        echo -e "${RED}❌ Database har ingen tabeller${NC}"
    fi
else
    echo -e "${RED}❌ PostgreSQL database ikke tilgjengelig${NC}"
fi

echo ""

# Sjekk filer
echo -e "${YELLOW}📁 Viktige filer:${NC}"
files=(
    "/home/$USER/shopify_royalties/organized_shopify_backup.py"
    "/home/$USER/shopify_royalties/index.html"
    "/home/$USER/shopify_royalties/shopify_database_viewer.html"
    "/home/$USER/shopify_royalties/start_dashboard.sh"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $(basename "$file") finnes${NC}"
    else
        echo -e "${RED}❌ $(basename "$file") mangler${NC}"
    fi
done

echo ""

# Sammendrag
IP=$(ip route get 1.1.1.1 | awk '{print $7}' | head -1)
echo -e "${YELLOW}🌐 Tilgang fra din PC:${NC}"
echo "📋 Dashboard Hub: http://$IP:8080/index.html"
echo "🗄️ pgAdmin: http://$IP:5050"
echo "📊 Database Viewer: http://$IP:8080/shopify_database_viewer.html"

echo ""
echo -e "${YELLOW}🔄 For å starte manuelt:${NC}"
echo "/home/$USER/shopify_royalties/start_dashboard.sh"

echo ""
echo "================================================"