# Database Configuration Template
# Copy this file to database_config.py and edit with your actual values

# PostgreSQL Connection Settings
DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "shopifydata",
    "user": "shopifyuser", 
    "password": "shopify_secure_password_2025",
    "sslmode": "prefer"
}

# Connection Pool Settings
CONNECTION_POOL = {
    "min_connections": 2,
    "max_connections": 10,
    "connection_timeout": 30,
    "idle_timeout": 300
}

# Database Performance Settings
PERFORMANCE = {
    "batch_size": 1000,
    "commit_interval": 100,
    "vacuum_threshold": 10000,
    "analyze_threshold": 5000
}

# Table Settings
TABLE_CONFIG = {
    "use_partitioning": True,  # Partition large tables by date
    "partition_by": "created_at",
    "partition_interval": "month",
    "retention_months": 24  # Keep data for 2 years
}

# Backup Settings
BACKUP_CONFIG = {
    "enabled": True,
    "schedule": "daily",
    "retention_days": 30,
    "compress": True,
    "backup_path": "./backups/database"
}

# Monitoring Settings
MONITORING = {
    "log_slow_queries": True,
    "slow_query_threshold": 5.0,  # seconds
    "enable_query_stats": True,
    "stats_retention_days": 7
}

# Development/Testing Override
# Uncomment for development environment
# DATABASE_CONFIG["database"] = "shopifydata_dev"
# DATABASE_CONFIG["host"] = "localhost"