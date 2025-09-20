#!/bin/bash
# Shopify Royalties Management System - Master Setup Script
# This script sets up the complete system on Ubuntu/Debian

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root. Please run as a regular user with sudo privileges."
fi

# Check for sudo privileges
if ! sudo -n true 2>/dev/null; then
    error "This script requires sudo privileges. Please ensure you can run sudo commands."
fi

log "🚀 Starting Shopify Royalties Management System Setup"
log "=================================================="

# System information
log "System Information:"
log "- OS: $(lsb_release -d | cut -f2)"
log "- Kernel: $(uname -r)"
log "- Architecture: $(uname -m)"
log "- User: $(whoami)"
log "- Home: $HOME"

# Create project directory
PROJECT_DIR="$HOME/shopify_royalties_system"
if [ ! -d "$PROJECT_DIR" ]; then
    log "Creating project directory: $PROJECT_DIR"
    mkdir -p "$PROJECT_DIR"
fi

cd "$PROJECT_DIR"

# Update system packages
log "📦 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install required system packages
log "🔧 Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    postgresql-client \
    docker.io \
    docker-compose \
    nginx \
    curl \
    wget \
    git \
    htop \
    tree \
    nano \
    cron \
    logrotate \
    unzip \
    build-essential \
    libpq-dev \
    python3-dev

# Add user to docker group
log "🐳 Configuring Docker permissions..."
sudo usermod -aG docker $USER
log "Note: You may need to log out and back in for Docker group membership to take effect"

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Create Python virtual environment
log "🐍 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python packages
if [ -f "requirements.txt" ]; then
    log "📚 Installing Python dependencies..."
    pip install -r requirements.txt
else
    warning "requirements.txt not found. Installing basic packages..."
    pip install requests psycopg2-binary pandas plotly pytz python-dotenv
fi

# Create directory structure
log "📁 Creating directory structure..."
mkdir -p {logs,config,backup_data,sql,scripts,web,docs,tests}
mkdir -p backup_data/{orders,products,collections,customers}
mkdir -p logs/{application,sync,system,error}

# Copy configuration files
log "⚙️ Setting up configuration files..."
if [ -f "config/shopify_config.template.py" ] && [ ! -f "config/shopify_config.py" ]; then
    cp config/shopify_config.template.py config/shopify_config.py
    log "Created config/shopify_config.py - Please edit with your Shopify credentials"
fi

if [ -f "config/database_config.template.py" ] && [ ! -f "config/database_config.py" ]; then
    cp config/database_config.template.py config/database_config.py
    log "Created config/database_config.py"
fi

# Create environment file
if [ ! -f ".env" ]; then
    log "🔐 Creating environment file..."
    cat > .env << 'EOF'
# Shopify Royalties System Environment Variables
SHOPIFY_STORE_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=your-access-token
DATABASE_URL=postgresql://shopifyuser:shopify_secure_password_2025@localhost:5433/shopifydata
LOG_LEVEL=INFO
ENVIRONMENT=production
EOF
    log "Created .env file - Please edit with your actual values"
fi

# Set up Docker Compose
if [ -f "docker-compose.yml" ]; then
    log "🐳 Setting up Docker containers..."
    
    # Create SQL initialization script
    if [ ! -f "sql/init.sql" ]; then
        log "Creating database initialization script..."
        cat > sql/init.sql << 'EOF'
-- Shopify Royalties Database Initialization
-- This script creates the necessary tables and indexes

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable row level security
ALTER DATABASE shopifydata SET row_security = on;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS shopify;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS logs;

-- Set search path
ALTER DATABASE shopifydata SET search_path TO shopify, public;

-- Create sequences
CREATE SEQUENCE IF NOT EXISTS shopify.order_seq;
CREATE SEQUENCE IF NOT EXISTS shopify.product_seq;
CREATE SEQUENCE IF NOT EXISTS shopify.customer_seq;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE shopifydata TO shopifyuser;
GRANT ALL PRIVILEGES ON SCHEMA shopify TO shopifyuser;
GRANT ALL PRIVILEGES ON SCHEMA analytics TO shopifyuser;
GRANT ALL PRIVILEGES ON SCHEMA logs TO shopifyuser;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA shopify TO shopifyuser;

-- Create basic tables (will be expanded by application)
CREATE TABLE IF NOT EXISTS shopify.sync_status (
    id SERIAL PRIMARY KEY,
    sync_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    records_processed INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    error_details TEXT
);

-- Insert initial status
INSERT INTO shopify.sync_status (sync_type, status) 
VALUES ('initial_setup', 'completed') 
ON CONFLICT DO NOTHING;
EOF
    fi
    
    # Start Docker containers
    docker-compose up -d
    
    # Wait for database to be ready
    log "⏳ Waiting for database to be ready..."
    sleep 30
    
    # Check if containers are running
    if docker-compose ps | grep -q "Up"; then
        success "Docker containers are running"
    else
        error "Failed to start Docker containers"
    fi
else
    warning "docker-compose.yml not found. Skipping Docker setup."
fi

# Create systemd service
log "🔧 Creating systemd service..."
cat > /tmp/shopify-dashboard.service << EOF
[Unit]
Description=Shopify Royalties Dashboard Services
After=docker.service postgresql.service network.target
Requires=docker.service
Wants=postgresql.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=$USER
Group=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=$PROJECT_DIR/scripts/start_dashboard.sh
ExecStop=$PROJECT_DIR/scripts/stop_dashboard.sh
TimeoutStartSec=300
TimeoutStopSec=60

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/shopify-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable shopify-dashboard

# Create startup script
log "📜 Creating startup scripts..."
mkdir -p scripts

cat > scripts/start_dashboard.sh << 'EOF'
#!/bin/bash
# Shopify Royalties Dashboard Startup Script

cd "$(dirname "$0")/.."
source venv/bin/activate

LOG_FILE="logs/system/startup.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "$(date): $1" | tee -a "$LOG_FILE"
}

log "🚀 Starting Shopify Royalties Dashboard Services"

# Start Docker containers if not running
if ! docker-compose ps | grep -q "Up"; then
    log "Starting Docker containers..."
    docker-compose up -d
fi

# Wait for database
log "Waiting for database..."
for i in {1..30}; do
    if pg_isready -h localhost -p 5433 -U shopifyuser -d shopifydata > /dev/null 2>&1; then
        break
    fi
    sleep 2
done

# Start web dashboard
log "Starting web dashboard..."
pkill -f "python3 -m http.server 8080" 2>/dev/null || true
cd web 2>/dev/null || cd .
python3 -m http.server 8080 --bind 0.0.0.0 > /dev/null 2>&1 &
WEBSERVER_PID=$!
echo $WEBSERVER_PID > /tmp/shopify_webserver.pid

log "✅ Dashboard started on port 8080"
log "✅ pgAdmin available on port 5050"
log "🎉 Shopify Royalties System is ready!"
EOF

cat > scripts/stop_dashboard.sh << 'EOF'
#!/bin/bash
# Shopify Royalties Dashboard Stop Script

LOG_FILE="logs/system/shutdown.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "$(date): $1" | tee -a "$LOG_FILE"
}

log "🛑 Stopping Shopify Royalties Dashboard Services"

# Stop web server
if [ -f /tmp/shopify_webserver.pid ]; then
    PID=$(cat /tmp/shopify_webserver.pid)
    if ps -p $PID > /dev/null; then
        kill $PID
        log "Stopped web server (PID: $PID)"
    fi
    rm -f /tmp/shopify_webserver.pid
fi

# Stop other processes
pkill -f "python3 -m http.server 8080" 2>/dev/null || true

log "✅ Dashboard services stopped"
EOF

chmod +x scripts/start_dashboard.sh scripts/stop_dashboard.sh

# Create service check script
cat > scripts/check_services.sh << 'EOF'
#!/bin/bash
# Shopify Royalties Service Health Check

echo "🔍 SHOPIFY ROYALTIES SYSTEM STATUS"
echo "=================================="

# Check Docker containers
echo "🐳 Docker Containers:"
if command -v docker-compose &> /dev/null; then
    docker-compose ps 2>/dev/null || echo "  Docker Compose not available"
else
    echo "  Docker Compose not installed"
fi

# Check database connection
echo ""
echo "🗄️ Database:"
if pg_isready -h localhost -p 5433 -U shopifyuser > /dev/null 2>&1; then
    echo "  ✅ PostgreSQL is responding"
else
    echo "  ❌ PostgreSQL connection failed"
fi

# Check web services
echo ""
echo "🌐 Web Services:"
if netstat -tlnp 2>/dev/null | grep -q ":8080"; then
    echo "  ✅ Dashboard running on port 8080"
else
    echo "  ❌ Dashboard not running on port 8080"
fi

if netstat -tlnp 2>/dev/null | grep -q ":5050"; then
    echo "  ✅ pgAdmin running on port 5050"
else
    echo "  ❌ pgAdmin not running on port 5050"
fi

# Check systemd service
echo ""
echo "🔧 System Service:"
if systemctl is-active --quiet shopify-dashboard 2>/dev/null; then
    echo "  ✅ shopify-dashboard service is active"
else
    echo "  ❌ shopify-dashboard service is not active"
fi

echo ""
echo "=================================="
EOF

chmod +x scripts/check_services.sh

# Set up cron jobs
log "⏰ Setting up cron jobs..."
(crontab -l 2>/dev/null | grep -v "shopify_royalties"; cat << EOF

# Shopify Royalties System Automation
# Ensure services start after reboot
@reboot sleep 60 && $PROJECT_DIR/scripts/start_dashboard.sh

# Health check every 5 minutes
*/5 * * * * $PROJECT_DIR/scripts/check_services.sh > /dev/null 2>&1

# Daily sync at 2 AM (uncomment when ready)
# 0 2 * * * cd $PROJECT_DIR && source venv/bin/activate && python3 organized_shopify_backup.py --daily-sync

# Hourly quick sync (uncomment when ready)
# 0 * * * * cd $PROJECT_DIR && source venv/bin/activate && python3 organized_shopify_backup.py --quick-sync
EOF
) | crontab -

# Create log rotation
log "📝 Setting up log rotation..."
sudo cat > /etc/logrotate.d/shopify-royalties << EOF
$PROJECT_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    sharedscripts
    postrotate
        systemctl reload shopify-dashboard > /dev/null 2>&1 || true
    endscript
}

$PROJECT_DIR/logs/*/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
}
EOF

# Create simple health check endpoint
if [ ! -d "web" ]; then
    mkdir -p web
fi

# Copy existing HTML files or create basic ones
if [ -f "../shopify_royalties/index.html" ]; then
    cp ../shopify_royalties/index.html web/
    log "Copied existing dashboard HTML"
fi

if [ -f "../shopify_royalties/shopify_database_viewer.html" ]; then
    cp ../shopify_royalties/shopify_database_viewer.html web/
    log "Copied existing database viewer HTML"
fi

# Create basic index.html if none exists
if [ ! -f "web/index.html" ]; then
    cat > web/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Shopify Royalties Management System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h1 class="card-title mb-0">🛍️ Shopify Royalties System</h1>
                    </div>
                    <div class="card-body">
                        <p class="lead">Welcome to the Shopify Royalties Management System!</p>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="card mb-3">
                                    <div class="card-body">
                                        <h5 class="card-title">📊 Database Admin</h5>
                                        <p class="card-text">Access pgAdmin for database management</p>
                                        <a href="http://localhost:5050" class="btn btn-primary" target="_blank">Open pgAdmin</a>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card mb-3">
                                    <div class="card-body">
                                        <h5 class="card-title">🔍 System Status</h5>
                                        <p class="card-text">Check system health and services</p>
                                        <button class="btn btn-success" onclick="checkStatus()">Check Status</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="status-info" class="mt-3"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script>
        function checkStatus() {
            document.getElementById('status-info').innerHTML = '<div class="alert alert-info">System is running! ✅</div>';
        }
    </script>
</body>
</html>
EOF
fi

# Final system status check
log "🔍 Running final system check..."
sleep 5
bash scripts/check_services.sh

# Create quick reference
log "📖 Creating quick reference..."
cat > QUICK_START.md << 'EOF'
# Quick Start Guide

## Access Points
- **Dashboard**: http://localhost:8080
- **pgAdmin**: http://localhost:5050
  - Email: admin@your-domain.com
  - Password: admin123_secure_2025

## Configuration Files to Edit
1. `config/shopify_config.py` - Add your Shopify store credentials
2. `.env` - Set environment variables

## Useful Commands
```bash
# Check system status
./scripts/check_services.sh

# Start services manually
sudo systemctl start shopify-dashboard

# View logs
tail -f logs/system/startup.log

# Access database directly
psql postgresql://shopifyuser:shopify_secure_password_2025@localhost:5433/shopifydata
```

## Next Steps
1. Edit configuration files with your Shopify credentials
2. Test API connection
3. Run initial data sync
4. Set up automated synchronization
EOF

# Summary
log "🎉 Setup completed successfully!"
log "=================================================="
success "Shopify Royalties Management System is installed!"
log ""
log "📋 Next Steps:"
log "1. Edit config/shopify_config.py with your Shopify credentials"
log "2. Edit .env file with your environment settings"
log "3. Access dashboard: http://localhost:8080"
log "4. Access pgAdmin: http://localhost:5050"
log "5. Run initial data sync when ready"
log ""
log "📖 See QUICK_START.md for more information"
log "🔍 Run './scripts/check_services.sh' to verify system status"
log ""
warning "🔄 You may need to log out and back in for Docker group membership to take effect"

# Deactivate virtual environment
deactivate 2>/dev/null || true

log "✅ Setup script completed!"