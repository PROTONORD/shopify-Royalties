#!/bin/bash
# PROTONORD Shopify Dashboard Startup Script
# Starter alle nødvendige tjenester for Shopify dashboard

LOG_FILE="/home/kau005/protonord_no/logs/startup.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "$(date): $1" >> "$LOG_FILE"
}

log "🚀 STARTER PROTONORD SHOPIFY DASHBOARD TJENESTER"

# Vent på at docker er klar
log "Venter på Docker..."
while ! docker info > /dev/null 2>&1; do
    sleep 2
done

# Vent på at PostgreSQL er klar
log "Venter på PostgreSQL..."
while ! pg_isready -h localhost -p 5433 -U shopifyuser > /dev/null 2>&1; do
    sleep 2
done

# Start pgAdmin (bare hvis den ikke allerede kjører)
if docker ps | grep -q pgadmin; then
    log "pgAdmin kjører allerede"
else
    log "Starter pgAdmin..."
    docker stop pgadmin 2>/dev/null || true
    docker rm pgadmin 2>/dev/null || true
    
    docker run -d --name pgadmin \
        -p 0.0.0.0:5050:80 \
        -e PGADMIN_DEFAULT_EMAIL=admin@protonord.no \
        -e PGADMIN_DEFAULT_PASSWORD=admin123 \
        dpage/pgadmin4 >> "$LOG_FILE" 2>&1

    if [ $? -eq 0 ]; then
        log "✅ pgAdmin startet på port 5050"
    else
        log "❌ Feil ved start av pgAdmin"
    fi
fi

# Start webserver (bare hvis den ikke allerede kjører)
if netstat -tlnp | grep -q ":8080"; then
    log "Webserver kjører allerede på port 8080"
else
    log "Starter webserver..."
    pkill -f "http.server 8080" 2>/dev/null || true
    
    cd /home/kau005/protonord_no
    /usr/bin/python3 -m http.server 8080 --bind 0.0.0.0 > /dev/null 2>&1 &
    WEBSERVER_PID=$!

    if [ $? -eq 0 ]; then
        log "✅ Webserver startet på port 8080 (PID: $WEBSERVER_PID)"
        echo $WEBSERVER_PID > /tmp/shopify_webserver.pid
    else
        log "❌ Feil ved start av webserver"
    fi
fi

# Vent litt og sjekk at alt kjører
sleep 10

# Sjekk pgAdmin
if docker ps | grep pgadmin > /dev/null; then
    log "✅ pgAdmin kjører: http://$(hostname -I | awk '{print $1}'):5050"
else
    log "❌ pgAdmin kjører ikke"
fi

# Sjekk webserver
if netstat -tlnp | grep ":8080" > /dev/null; then
    log "✅ Webserver kjører: http://$(hostname -I | awk '{print $1}'):8080"
else
    log "❌ Webserver kjører ikke"
fi

log "🎉 OPPSTART FULLFØRT - Sjekk status på: http://$(hostname -I | awk '{print $1}'):8080"