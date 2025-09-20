# Shopify Royalty Management System Configuration
# Copy this file to 'shopify_config.py' and fill in your actual values

# Shopify Store Configuration
SHOPIFY_STORE_NAME = "your-store-name"
SHOPIFY_ACCESS_TOKEN = "your-private-app-access-token"

# Shopify API Settings
SHOPIFY_API_VERSION = "2024-01"  # Use latest stable version
SHOPIFY_TIMEOUT = 30  # Request timeout in seconds
SHOPIFY_RATE_LIMIT_DELAY = 0.5  # Delay between requests in seconds

# Pagination Settings
ORDERS_PER_PAGE = 250  # Max 250 per Shopify API
PRODUCTS_PER_PAGE = 250
CUSTOMERS_PER_PAGE = 250
COLLECTIONS_PER_PAGE = 250

# Date Range for Initial Sync (if not syncing all historical data)
# Set to None for complete historical sync
INITIAL_SYNC_DAYS = None  # or set to number like 365 for last year only

# Data Processing Options
INCLUDE_DRAFT_ORDERS = True
INCLUDE_ARCHIVED_PRODUCTS = True
INCLUDE_CUSTOMER_ADDRESSES = True
INCLUDE_ORDER_FULFILLMENTS = True

# File Organization Settings
BACKUP_BASE_PATH = "./backup_data"
ORGANIZE_BY_DATE = True  # Organize orders by date
DATE_FORMAT = "%Y/%B"  # Year/Month format (e.g., 2025/january)

# Error Handling
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY = 2  # Seconds between retries
CONTINUE_ON_ERROR = True  # Continue processing even if some items fail

# Logging Configuration
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_TO_FILE = True
LOG_FILE_PATH = "./logs/shopify_sync.log"
LOG_MAX_SIZE = 10  # MB
LOG_BACKUP_COUNT = 5

# Webhook Configuration (for real-time updates)
WEBHOOK_SECRET = "your-webhook-secret-key"
WEBHOOK_TOPICS = [
    "orders/create",
    "orders/updated", 
    "orders/paid",
    "orders/cancelled",
    "products/create",
    "products/update",
    "customers/create",
    "customers/update"
]

# Performance Tuning
ENABLE_COMPRESSION = True
BATCH_SIZE = 100  # Records to process in each batch
CONCURRENT_REQUESTS = 5  # Number of parallel API requests

# Security Settings
ENCRYPT_SENSITIVE_DATA = False  # Set to True for production
ENCRYPTION_KEY = "your-32-byte-encryption-key-here"

# Notification Settings
ENABLE_EMAIL_NOTIFICATIONS = False
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "your-email@gmail.com"
SMTP_PASSWORD = "your-app-password"
NOTIFICATION_RECIPIENTS = ["admin@yourcompany.com"]

# Backup and Archival
ENABLE_AUTO_BACKUP = True
BACKUP_RETENTION_DAYS = 90
COMPRESS_OLD_BACKUPS = True

# Feature Flags
ENABLE_REALTIME_SYNC = True
ENABLE_ANALYTICS = True
ENABLE_REPORTING = True
ENABLE_WEB_DASHBOARD = True