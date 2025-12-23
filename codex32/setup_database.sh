#!/usr/bin/env bash
# Codex-32 Database Setup Script
# Creates PostgreSQL database and tables for local development

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Codex-32 Database Setup (PostgreSQL)                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "Error: PostgreSQL is not installed"
    echo "Install it with:"
    echo "  macOS: brew install postgresql"
    echo "  Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib"
    echo "  CentOS/RHEL: sudo yum install postgresql-server postgresql-contrib"
    exit 1
fi

# Check if PostgreSQL server is running
if ! pg_isready -U postgres > /dev/null 2>&1; then
    echo "Error: PostgreSQL server is not running"
    echo "Start it with:"
    echo "  macOS: brew services start postgresql"
    echo "  Ubuntu/Debian: sudo systemctl start postgresql"
    exit 1
fi

echo "✓ PostgreSQL is installed and running"
echo ""

# Configuration
DB_USER="codex_user"
DB_PASSWORD="codex_password"  # Change in production!
DB_NAME="codex32"
DB_HOST="localhost"

echo "Database Configuration:"
echo "  Host: $DB_HOST"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo ""

# Create database
echo "Creating database '$DB_NAME'..."
psql -U postgres -h "$DB_HOST" -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
psql -U postgres -h "$DB_HOST" -c "CREATE DATABASE $DB_NAME;"
echo "✓ Database created/already exists"

# Create user
echo "Creating user '$DB_USER'..."
psql -U postgres -h "$DB_HOST" -tc "SELECT 1 FROM pg_user WHERE usename = '$DB_USER'" | grep -q 1 || \
psql -U postgres -h "$DB_HOST" -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
echo "✓ User created/already exists"

# Grant permissions
echo "Granting permissions..."
psql -U postgres -h "$DB_HOST" -c "ALTER ROLE $DB_USER WITH CREATEDB;"
psql -U postgres -h "$DB_HOST" -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
psql -U postgres -h "$DB_HOST" -d "$DB_NAME" -c "GRANT ALL ON SCHEMA public TO $DB_USER;"
echo "✓ Permissions granted"

# Create tables
echo "Creating tables..."
psql -U "$DB_USER" -h "$DB_HOST" -d "$DB_NAME" << 'EOF'
-- Bots table
CREATE TABLE IF NOT EXISTS bots (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(50) DEFAULT '1.0.0',
    role VARCHAR(50) DEFAULT 'worker',
    blueprint VARCHAR(512) NOT NULL,
    status VARCHAR(50) DEFAULT 'registered',
    process_id INTEGER,
    k8s_pod_name VARCHAR(255),
    cpu_load FLOAT DEFAULT 0.0,
    memory_usage_mb FLOAT DEFAULT 0.0,
    uptime_seconds BIGINT DEFAULT 0,
    error_rate FLOAT DEFAULT 0.0,
    requests_per_second FLOAT DEFAULT 0.0,
    last_error TEXT,
    error_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    stopped_at TIMESTAMP,
    last_heartbeat TIMESTAMP
);

-- Bot deployment configs table
CREATE TABLE IF NOT EXISTS bot_deployment_configs (
    bot_id VARCHAR(255) PRIMARY KEY REFERENCES bots(id) ON DELETE CASCADE,
    deployment_type VARCHAR(50) DEFAULT 'local_process',
    image_uri VARCHAR(512),
    cpu_request VARCHAR(50) DEFAULT '100m',
    cpu_limit VARCHAR(50) DEFAULT '500m',
    memory_request VARCHAR(50) DEFAULT '128Mi',
    memory_limit VARCHAR(50) DEFAULT '512Mi',
    replicas INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bot logs table
CREATE TABLE IF NOT EXISTS bot_logs (
    id SERIAL PRIMARY KEY,
    bot_id VARCHAR(255) NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
    level VARCHAR(20),
    message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    hashed_password VARCHAR(255),
    roles VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    service_name VARCHAR(255),
    roles VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP
);

-- Performance metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    bot_id VARCHAR(255) NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
    metric_name VARCHAR(100),
    value FLOAT,
    unit VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_bots_status ON bots(status);
CREATE INDEX IF NOT EXISTS idx_bots_role ON bots(role);
CREATE INDEX IF NOT EXISTS idx_bot_logs_bot_id ON bot_logs(bot_id);
CREATE INDEX IF NOT EXISTS idx_bot_logs_timestamp ON bot_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_metrics_bot_id ON performance_metrics(bot_id);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON performance_metrics(timestamp);

EOF

echo "✓ Tables created/already exist"
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║            Database Setup Complete! ✓                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo "Database Details:"
echo "  Connection String: postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:5432/$DB_NAME"
echo "  Async URL: postgresql+asyncpg://$DB_USER:$DB_PASSWORD@$DB_HOST:5432/$DB_NAME"
echo ""

echo "Update your .env file with:"
echo "  DATABASE_URL=postgresql+asyncpg://$DB_USER:$DB_PASSWORD@$DB_HOST:5432/$DB_NAME"
echo ""
