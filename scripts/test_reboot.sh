#!/bin/bash
# Shopify Royalties Dashboard Reboot Test
# Simulerer reboot ved å stoppe alle tjenester og starte de på nytt

echo "🔄 SIMULERER REBOOT - STOPPER ALLE TJENESTER"
echo "================================================"

# Stopp systemd service
echo "Stopper systemd service..."
sudo systemctl stop shopify-dashboard

# Stopp Docker containers
echo "Stopper Docker containers..."
docker stop pgladmin 2>/dev/null || true
docker rm pgladmin 2>/dev/null || true

# Stopp webserver
echo "Stopper webserver..."
pkill -f "http.server 8080" 2>/dev/null || true

echo -e "\n⏱️  Venter 5 sekunder...\n"
sleep 5

echo "🚀 SIMULERER OPPSTART ETTER REBOOT"
echo "================================================"

# Start systemd service (simulerer automatisk oppstart)
echo "Starter systemd service (simulerer oppstart etter reboot)..."
sudo systemctl start shopify-dashboard

echo -e "\n⏱️  Venter 10 sekunder på at alt skal starte...\n"
sleep 10

echo "📊 SJEKKER STATUS ETTER 'REBOOT'"
echo "================================================"

# Kjør service-sjekk
./check_services.sh

echo -e "\n🎯 REBOOT-TEST FULLFØRT!"
echo "================================================"
echo "Hvis alle tjenester viser ✅ over, så fungerer automatisk oppstart!"