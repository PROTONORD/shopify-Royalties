-- Shopify Royalty Database Schema
-- Complete database schema for Shopify data management

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas for better organization
CREATE SCHEMA IF NOT EXISTS shopify;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS logs;

-- Set default search path
ALTER DATABASE shopifydata SET search_path TO shopify, public;

-- ========================================
-- SHOPIFY CORE TABLES
-- ========================================

-- Products table
CREATE TABLE IF NOT EXISTS shopify.products (
    id BIGINT PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    handle VARCHAR(255) UNIQUE,
    product_type VARCHAR(255),
    vendor VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    published_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50),
    tags TEXT,
    body_html TEXT,
    options JSONB,
    images JSONB,
    variants JSONB,
    seo_title VARCHAR(255),
    seo_description TEXT,
    template_suffix VARCHAR(100),
    published_scope VARCHAR(50),
    admin_graphql_api_id VARCHAR(255),
    raw_data JSONB,
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Product variants table
CREATE TABLE IF NOT EXISTS shopify.product_variants (
    id BIGINT PRIMARY KEY,
    product_id BIGINT REFERENCES shopify.products(id),
    title VARCHAR(500),
    price DECIMAL(10,2),
    compare_at_price DECIMAL(10,2),
    sku VARCHAR(255),
    position INTEGER,
    inventory_policy VARCHAR(50),
    fulfillment_service VARCHAR(100),
    inventory_management VARCHAR(100),
    option1 VARCHAR(255),
    option2 VARCHAR(255),
    option3 VARCHAR(255),
    taxable BOOLEAN,
    barcode VARCHAR(255),
    grams INTEGER,
    weight DECIMAL(10,3),
    weight_unit VARCHAR(10),
    inventory_item_id BIGINT,
    inventory_quantity INTEGER,
    old_inventory_quantity INTEGER,
    requires_shipping BOOLEAN,
    admin_graphql_api_id VARCHAR(255),
    image_id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    raw_data JSONB,
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Collections table
CREATE TABLE IF NOT EXISTS shopify.collections (
    id BIGINT PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    handle VARCHAR(255) UNIQUE,
    description TEXT,
    published_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE,
    sort_order VARCHAR(50),
    template_suffix VARCHAR(100),
    products_count INTEGER DEFAULT 0,
    collection_type VARCHAR(50),
    published_scope VARCHAR(50),
    admin_graphql_api_id VARCHAR(255),
    image JSONB,
    rules JSONB,
    raw_data JSONB,
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Collection products relationship
CREATE TABLE IF NOT EXISTS shopify.collection_products (
    collection_id BIGINT REFERENCES shopify.collections(id),
    product_id BIGINT REFERENCES shopify.products(id),
    position INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (collection_id, product_id)
);

-- Customers table
CREATE TABLE IF NOT EXISTS shopify.customers (
    id BIGINT PRIMARY KEY,
    email VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    phone VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    orders_count INTEGER DEFAULT 0,
    state VARCHAR(50),
    total_spent DECIMAL(10,2),
    last_order_id BIGINT,
    note TEXT,
    verified_email BOOLEAN,
    multipass_identifier VARCHAR(255),
    tax_exempt BOOLEAN,
    tags TEXT,
    last_order_name VARCHAR(100),
    currency VARCHAR(3),
    accepts_marketing BOOLEAN,
    accepts_marketing_updated_at TIMESTAMP WITH TIME ZONE,
    marketing_opt_in_level VARCHAR(50),
    sms_marketing_consent JSONB,
    admin_graphql_api_id VARCHAR(255),
    default_address JSONB,
    addresses JSONB,
    raw_data JSONB,
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Orders table (partitioned by created_at)
CREATE TABLE IF NOT EXISTS shopify.orders (
    id BIGINT PRIMARY KEY,
    order_number INTEGER,
    name VARCHAR(100),
    email VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    closed_at TIMESTAMP WITH TIME ZONE,
    processed_at TIMESTAMP WITH TIME ZONE,
    customer_id BIGINT REFERENCES shopify.customers(id),
    financial_status VARCHAR(50),
    fulfillment_status VARCHAR(50),
    gateway VARCHAR(100),
    test BOOLEAN DEFAULT FALSE,
    total_price DECIMAL(10,2),
    subtotal_price DECIMAL(10,2),
    total_weight INTEGER,
    total_tax DECIMAL(10,2),
    taxes_included BOOLEAN,
    currency VARCHAR(3),
    total_discounts DECIMAL(10,2),
    total_line_items_price DECIMAL(10,2),
    cart_token VARCHAR(255),
    buyer_accepts_marketing BOOLEAN,
    referring_site VARCHAR(500),
    landing_site VARCHAR(500),
    cancelled_reason VARCHAR(100),
    cancel_reason VARCHAR(100),
    user_id BIGINT,
    location_id BIGINT,
    source_identifier VARCHAR(255),
    source_url VARCHAR(500),
    device_id BIGINT,
    phone VARCHAR(50),
    customer_locale VARCHAR(10),
    app_id BIGINT,
    browser_ip INET,
    client_details JSONB,
    payment_gateway_names JSONB,
    processing_method VARCHAR(50),
    checkout_id BIGINT,
    source_name VARCHAR(100),
    fulfillment_status_label VARCHAR(100),
    checkout_token VARCHAR(255),
    reference VARCHAR(255),
    number INTEGER,
    token VARCHAR(255),
    billing_address JSONB,
    shipping_address JSONB,
    line_items JSONB,
    shipping_lines JSONB,
    tax_lines JSONB,
    payment_details JSONB,
    fulfillments JSONB,
    discount_codes JSONB,
    discount_applications JSONB,
    refunds JSONB,
    admin_graphql_api_id VARCHAR(255),
    raw_data JSONB,
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Order line items table
CREATE TABLE IF NOT EXISTS shopify.order_line_items (
    id BIGINT PRIMARY KEY,
    order_id BIGINT REFERENCES shopify.orders(id),
    product_id BIGINT REFERENCES shopify.products(id),
    variant_id BIGINT REFERENCES shopify.product_variants(id),
    title VARCHAR(500),
    quantity INTEGER,
    sku VARCHAR(255),
    variant_title VARCHAR(255),
    vendor VARCHAR(255),
    fulfillment_service VARCHAR(100),
    fulfillment_status VARCHAR(50),
    requires_shipping BOOLEAN,
    taxable BOOLEAN,
    gift_card BOOLEAN,
    name VARCHAR(500),
    variant_inventory_management VARCHAR(100),
    properties JSONB,
    product_exists BOOLEAN,
    fulfillable_quantity INTEGER,
    grams INTEGER,
    price DECIMAL(10,2),
    total_discount DECIMAL(10,2),
    fulfillment_status_label VARCHAR(100),
    tip_payment_gateway VARCHAR(100),
    tip_payment_method VARCHAR(100),
    tax_lines JSONB,
    discount_allocations JSONB,
    duties JSONB,
    admin_graphql_api_id VARCHAR(255),
    raw_data JSONB,
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- ANALYTICS AND REPORTING TABLES
-- ========================================

-- Sync status tracking
CREATE TABLE IF NOT EXISTS analytics.sync_status (
    id SERIAL PRIMARY KEY,
    sync_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    records_processed INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    error_details TEXT,
    last_cursor VARCHAR(255),
    metadata JSONB
);

-- Daily sales summary
CREATE TABLE IF NOT EXISTS analytics.daily_sales (
    date DATE PRIMARY KEY,
    total_orders INTEGER DEFAULT 0,
    total_revenue DECIMAL(12,2) DEFAULT 0,
    total_items INTEGER DEFAULT 0,
    unique_customers INTEGER DEFAULT 0,
    average_order_value DECIMAL(10,2) DEFAULT 0,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Product performance metrics
CREATE TABLE IF NOT EXISTS analytics.product_performance (
    product_id BIGINT REFERENCES shopify.products(id),
    period_start DATE,
    period_end DATE,
    units_sold INTEGER DEFAULT 0,
    revenue DECIMAL(12,2) DEFAULT 0,
    orders_count INTEGER DEFAULT 0,
    refunds_count INTEGER DEFAULT 0,
    refunded_amount DECIMAL(10,2) DEFAULT 0,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (product_id, period_start, period_end)
);

-- Customer lifetime value
CREATE TABLE IF NOT EXISTS analytics.customer_ltv (
    customer_id BIGINT REFERENCES shopify.customers(id) PRIMARY KEY,
    first_order_date DATE,
    last_order_date DATE,
    total_orders INTEGER DEFAULT 0,
    total_spent DECIMAL(12,2) DEFAULT 0,
    average_order_value DECIMAL(10,2) DEFAULT 0,
    days_as_customer INTEGER DEFAULT 0,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- LOGGING AND MONITORING
-- ========================================

-- Error logs
CREATE TABLE IF NOT EXISTS logs.error_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR(20),
    source VARCHAR(100),
    message TEXT,
    details JSONB,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- API call logs
CREATE TABLE IF NOT EXISTS logs.api_calls (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    status_code INTEGER,
    response_time_ms INTEGER,
    rate_limit_remaining INTEGER,
    rate_limit_reset TIMESTAMP WITH TIME ZONE,
    error_message TEXT
);

-- ========================================
-- INDEXES FOR PERFORMANCE
-- ========================================

-- Products indexes
CREATE INDEX IF NOT EXISTS idx_products_handle ON shopify.products(handle);
CREATE INDEX IF NOT EXISTS idx_products_vendor ON shopify.products(vendor);
CREATE INDEX IF NOT EXISTS idx_products_type ON shopify.products(product_type);
CREATE INDEX IF NOT EXISTS idx_products_status ON shopify.products(status);
CREATE INDEX IF NOT EXISTS idx_products_created_at ON shopify.products(created_at);
CREATE INDEX IF NOT EXISTS idx_products_tags_gin ON shopify.products USING gin(to_tsvector('english', tags));

-- Product variants indexes
CREATE INDEX IF NOT EXISTS idx_variants_product_id ON shopify.product_variants(product_id);
CREATE INDEX IF NOT EXISTS idx_variants_sku ON shopify.product_variants(sku);
CREATE INDEX IF NOT EXISTS idx_variants_barcode ON shopify.product_variants(barcode);
CREATE INDEX IF NOT EXISTS idx_variants_inventory_item_id ON shopify.product_variants(inventory_item_id);

-- Collections indexes
CREATE INDEX IF NOT EXISTS idx_collections_handle ON shopify.collections(handle);
CREATE INDEX IF NOT EXISTS idx_collections_type ON shopify.collections(collection_type);

-- Customers indexes
CREATE INDEX IF NOT EXISTS idx_customers_email ON shopify.customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_created_at ON shopify.customers(created_at);
CREATE INDEX IF NOT EXISTS idx_customers_total_spent ON shopify.customers(total_spent);
CREATE INDEX IF NOT EXISTS idx_customers_orders_count ON shopify.customers(orders_count);

-- Orders indexes
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON shopify.orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON shopify.orders(created_at);
CREATE INDEX IF NOT EXISTS idx_orders_financial_status ON shopify.orders(financial_status);
CREATE INDEX IF NOT EXISTS idx_orders_fulfillment_status ON shopify.orders(fulfillment_status);
CREATE INDEX IF NOT EXISTS idx_orders_total_price ON shopify.orders(total_price);
CREATE INDEX IF NOT EXISTS idx_orders_email ON shopify.orders(email);
CREATE INDEX IF NOT EXISTS idx_orders_order_number ON shopify.orders(order_number);

-- Order line items indexes
CREATE INDEX IF NOT EXISTS idx_line_items_order_id ON shopify.order_line_items(order_id);
CREATE INDEX IF NOT EXISTS idx_line_items_product_id ON shopify.order_line_items(product_id);
CREATE INDEX IF NOT EXISTS idx_line_items_variant_id ON shopify.order_line_items(variant_id);
CREATE INDEX IF NOT EXISTS idx_line_items_sku ON shopify.order_line_items(sku);

-- Analytics indexes
CREATE INDEX IF NOT EXISTS idx_sync_status_type ON analytics.sync_status(sync_type);
CREATE INDEX IF NOT EXISTS idx_sync_status_started ON analytics.sync_status(started_at);
CREATE INDEX IF NOT EXISTS idx_daily_sales_date ON analytics.daily_sales(date);

-- Logs indexes
CREATE INDEX IF NOT EXISTS idx_error_log_timestamp ON logs.error_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_error_log_level ON logs.error_log(level);
CREATE INDEX IF NOT EXISTS idx_api_calls_timestamp ON logs.api_calls(timestamp);
CREATE INDEX IF NOT EXISTS idx_api_calls_endpoint ON logs.api_calls(endpoint);

-- ========================================
-- FUNCTIONS AND TRIGGERS
-- ========================================

-- Function to update product counts in collections
CREATE OR REPLACE FUNCTION shopify.update_collection_product_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE shopify.collections 
        SET products_count = products_count + 1 
        WHERE id = NEW.collection_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE shopify.collections 
        SET products_count = products_count - 1 
        WHERE id = OLD.collection_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger for collection product count
DROP TRIGGER IF EXISTS collection_product_count_trigger ON shopify.collection_products;
CREATE TRIGGER collection_product_count_trigger
    AFTER INSERT OR DELETE ON shopify.collection_products
    FOR EACH ROW EXECUTE FUNCTION shopify.update_collection_product_count();

-- Function to calculate customer LTV
CREATE OR REPLACE FUNCTION analytics.calculate_customer_ltv(customer_id_param BIGINT)
RETURNS VOID AS $$
DECLARE
    first_order DATE;
    last_order DATE;
    total_orders_count INTEGER;
    total_amount DECIMAL(12,2);
    avg_order_val DECIMAL(10,2);
    days_customer INTEGER;
BEGIN
    SELECT 
        MIN(created_at::date),
        MAX(created_at::date),
        COUNT(*),
        SUM(total_price),
        AVG(total_price)
    INTO first_order, last_order, total_orders_count, total_amount, avg_order_val
    FROM shopify.orders 
    WHERE customer_id = customer_id_param AND financial_status = 'paid';
    
    days_customer := COALESCE(last_order - first_order, 0);
    
    INSERT INTO analytics.customer_ltv 
    (customer_id, first_order_date, last_order_date, total_orders, total_spent, 
     average_order_value, days_as_customer, calculated_at)
    VALUES 
    (customer_id_param, first_order, last_order, COALESCE(total_orders_count, 0), 
     COALESCE(total_amount, 0), COALESCE(avg_order_val, 0), days_customer, CURRENT_TIMESTAMP)
    ON CONFLICT (customer_id) DO UPDATE SET
        first_order_date = EXCLUDED.first_order_date,
        last_order_date = EXCLUDED.last_order_date,
        total_orders = EXCLUDED.total_orders,
        total_spent = EXCLUDED.total_spent,
        average_order_value = EXCLUDED.average_order_value,
        days_as_customer = EXCLUDED.days_as_customer,
        calculated_at = EXCLUDED.calculated_at;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- PERMISSIONS
-- ========================================

-- Grant permissions to shopifyuser
GRANT ALL PRIVILEGES ON DATABASE shopifydata TO shopifyuser;
GRANT ALL PRIVILEGES ON SCHEMA shopify TO shopifyuser;
GRANT ALL PRIVILEGES ON SCHEMA analytics TO shopifyuser;
GRANT ALL PRIVILEGES ON SCHEMA logs TO shopifyuser;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA shopify TO shopifyuser;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA analytics TO shopifyuser;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA logs TO shopifyuser;

GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA shopify TO shopifyuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA analytics TO shopifyuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA logs TO shopifyuser;

-- Grant usage on sequences for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA shopify GRANT ALL ON TABLES TO shopifyuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT ALL ON TABLES TO shopifyuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA logs GRANT ALL ON TABLES TO shopifyuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA shopify GRANT ALL ON SEQUENCES TO shopifyuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT ALL ON SEQUENCES TO shopifyuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA logs GRANT ALL ON SEQUENCES TO shopifyuser;

-- ========================================
-- INITIAL DATA
-- ========================================

-- Insert initial sync status
INSERT INTO analytics.sync_status (sync_type, status, completed_at, records_processed) 
VALUES ('database_schema', 'completed', CURRENT_TIMESTAMP, 0) 
ON CONFLICT DO NOTHING;

-- ========================================
-- VIEWS FOR COMMON QUERIES
-- ========================================

-- Order summary view
CREATE OR REPLACE VIEW analytics.order_summary AS
SELECT 
    DATE_TRUNC('day', created_at) as order_date,
    COUNT(*) as total_orders,
    SUM(total_price) as total_revenue,
    AVG(total_price) as average_order_value,
    COUNT(DISTINCT customer_id) as unique_customers
FROM shopify.orders 
WHERE financial_status = 'paid'
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY order_date DESC;

-- Product sales view
CREATE OR REPLACE VIEW analytics.product_sales AS
SELECT 
    p.id,
    p.title,
    p.vendor,
    p.product_type,
    SUM(oli.quantity) as units_sold,
    SUM(oli.price * oli.quantity) as total_revenue,
    COUNT(DISTINCT oli.order_id) as orders_count
FROM shopify.products p
JOIN shopify.order_line_items oli ON p.id = oli.product_id
JOIN shopify.orders o ON oli.order_id = o.id
WHERE o.financial_status = 'paid'
GROUP BY p.id, p.title, p.vendor, p.product_type
ORDER BY total_revenue DESC;

-- Customer summary view
CREATE OR REPLACE VIEW analytics.customer_summary AS
SELECT 
    c.id,
    c.first_name,
    c.last_name,
    c.email,
    c.created_at as customer_since,
    COUNT(o.id) as total_orders,
    SUM(o.total_price) as total_spent,
    AVG(o.total_price) as average_order_value,
    MAX(o.created_at) as last_order_date
FROM shopify.customers c
LEFT JOIN shopify.orders o ON c.id = o.customer_id AND o.financial_status = 'paid'
GROUP BY c.id, c.first_name, c.last_name, c.email, c.created_at
ORDER BY total_spent DESC NULLS LAST;

-- Completion message
SELECT 'Shopify Royalty database schema created successfully!' as message;