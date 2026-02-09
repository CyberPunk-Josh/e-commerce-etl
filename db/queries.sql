-- Create database
CREATE DATABASE nelo;

-- List metric table
CREATE TABLE list_metrics (
    list_name VARCHAR PRIMARY KEY,

    -- Engagement metrics
    total_impressions INTEGER DEFAULT 0,
    unique_users INTEGER DEFAULT 0,
    total_clicks INTEGER DEFAULT 0,
    total_add_to_carts INTEGER DEFAULT 0,
    total_purchases INTEGER DEFAULT 0,

    -- Product diversity
    unique_products_shown INTEGER DEFAULT 0,

    -- Revenue metrics
    total_revenue DECIMAL(12,2) DEFAULT 0,
    avg_revenue_per_user DECIMAL(10,2),

    -- Calculated metrics
    ctr DECIMAL(5,4),
    engagement_rate DECIMAL(5,4),
    conversion_rate DECIMAL(5,4),
    bounce_rate DECIMAL(5,4),

    -- Metadata
    last_updated TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_list_metrics_engagement ON list_metrics(engagement_rate DESC);
CREATE INDEX idx_list_metrics_conversion ON list_metrics(conversion_rate DESC);
CREATE INDEX idx_list_metrics_revenue ON list_metrics(total_revenue DESC);

-- Products metrics table
CREATE TABLE product_metrics (
    product_id VARCHAR PRIMARY KEY,
    product_name VARCHAR,

    -- Impression metrics
    total_impressions INTEGER DEFAULT 0,
    unique_users_viewed INTEGER DEFAULT 0,

    -- Engagement metrics
    total_views INTEGER DEFAULT 0,
    total_clicks INTEGER DEFAULT 0,
    total_add_to_carts INTEGER DEFAULT 0,

    -- Conversion metrics
    total_purchases INTEGER DEFAULT 0,
    total_revenue DECIMAL(12,2) DEFAULT 0,

    -- Calculated metrics
    ctr DECIMAL(5,4),
    view_to_purchase_rate DECIMAL(5,4),
    conversion_rate DECIMAL(5,4),
    avg_price DECIMAL(10,2),

    -- Metadata
    first_seen TIMESTAMP,
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_product_metrics_ctr ON product_metrics(ctr DESC);
CREATE INDEX idx_product_metrics_conversion ON product_metrics(conversion_rate DESC);
CREATE INDEX idx_product_metrics_revenue ON product_metrics(total_revenue DESC);

-- EDA Queries
-- Top lists by engagement rate
SELECT
    list_name,
    unique_users,
    total_impressions,
    engagement_rate,
    conversion_rate,
    total_revenue
FROM list_metrics
ORDER BY engagement_rate DESC
LIMIT 10;

-- Best performing products by view-to-purchase rate
SELECT
    product_name,
    total_views,
    total_purchases,
    view_to_purchase_rate,
    total_revenue
FROM product_metrics
WHERE total_views >= (SELECT AVG(total_views) FROM product_metrics)
AND view_to_purchase_rate is not null
ORDER BY view_to_purchase_rate DESC
LIMIT 20;