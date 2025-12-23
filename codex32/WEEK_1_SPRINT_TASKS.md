# 🚀 WEEK 1 SPRINT TASKS - START NOW

**Week Duration:** Dec 23, 2025 - Dec 29, 2025 (or starting today if different date)  
**Phase:** 1 - Foundation  
**Objective:** Database setup, schema design, migration framework  
**Expected Result:** PostgreSQL with data, ORM models, database tests passing

---

## 📋 MONDAY MORNING CHECKLIST

```bash
# 1. Install PostgreSQL (if not present)
brew install postgresql@15
brew services start postgresql@15

# 2. Verify PostgreSQL is running
psql --version
psql -U postgres -c "SELECT 1"

# 3. Create development databases
createdb codex32_dev
createdb codex32_test

# 4. Create .env file
cat > .env << 'EOF'
DATABASE_URL=postgresql://localhost/codex32_dev
TEST_DATABASE_URL=postgresql://localhost/codex32_test
SECRET_KEY=dev-secret-key-change-in-production
OPENAI_API_KEY=sk-...  # Add your key later
ANTHROPIC_API_KEY=...  # Add your key later
EOF

# 5. Install Python dependencies
pip install sqlalchemy alembic psycopg2-binary python-jose passlib bcrypt

# 6. Verify installations
python -c "import sqlalchemy; print('✅ SQLAlchemy:', sqlalchemy.__version__)"
python -c "import psycopg2; print('✅ psycopg2 ready')"
```

---

## 🏗️ MONDAY AFTERNOON: DATABASE SCHEMA DESIGN

### Task 1: Create Base Models (1 hour)

**Create file: `app/models/base.py`**

Copy and paste this entire file:

```python
"""Database models base class and configuration"""

import os
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, Column, DateTime, String, UUID, Boolean, Integer, Float, Text, ForeignKey, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/codex32_dev")

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,  # Test connections before using
    pool_recycle=3600,   # Recycle connections hourly
    echo=False,          # Set to True for SQL logging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for models
Base = declarative_base()

def get_session() -> Session:
    """Get database session - use with Depends() in FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class UUIDMixin:
    """Mixin to add UUID primary key"""
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class NamedMixin:
    """Mixin to add name field"""
    name = Column(String(255), nullable=False, index=True)

# Initialize database
def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)

# Health check
def check_database() -> bool:
    """Check if database is accessible"""
    try:
        with SessionLocal() as session:
            session.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False
```

**Verify it works:**
```bash
python -c "
from app.models.base import engine, check_database
print('✅ Database connection successful' if check_database() else '❌ Connection failed')
"
```

### Task 2: Create User Model (45 min)

**Create file: `app/models/user.py`**

```python
"""User and authentication models"""

from enum import Enum
from sqlalchemy import Column, String, Boolean, Enum as SQLEnum, DateTime, UUID
from sqlalchemy.orm import relationship
from app.models.base import Base, UUIDMixin, TimestampMixin

class UserRole(str, Enum):
    """User roles"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    API_USER = "api_user"

class User(Base, UUIDMixin, TimestampMixin):
    """User model"""
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    workspace_id = Column(UUID, nullable=True)
    
    # Relationships
    bots = relationship("Bot", back_populates="owner", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(email={self.email}, username={self.username})>"

class APIKey(Base, UUIDMixin, TimestampMixin):
    """API key for programmatic access"""
    __tablename__ = "api_keys"
    
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False, index=True)
    key_hash = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    last_used_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    def __repr__(self) -> str:
        return f"<APIKey(name={self.name}, user_id={self.user_id})>"
```

**Test it:**
```bash
python -c "
from app.models.base import init_db
from app.models.user import User, UserRole
init_db()
print('✅ User model created successfully')
"
```

### Task 3: Create Bot Models (1 hour)

**Create file: `app/models/bot.py`**

```python
"""Bot and execution models"""

from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base, UUIDMixin, TimestampMixin

class Bot(Base, UUIDMixin, TimestampMixin):
    """Bot model"""
    __tablename__ = "bots"
    
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    code = Column(Text, nullable=False)
    config = Column(Text, nullable=True)  # YAML config as string
    owner_id = Column(UUID, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(50), default="inactive", index=True)  # inactive, active, error
    
    # Statistics
    execution_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    avg_execution_time_ms = Column(Float, default=0)
    last_executed_at = Column(DateTime, nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="bots")
    versions = relationship("BotVersion", back_populates="bot", cascade="all, delete-orphan")
    executions = relationship("BotExecution", back_populates="bot", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Bot(name={self.name}, status={self.status})>"

class BotVersion(Base, UUIDMixin, TimestampMixin):
    """Bot version history"""
    __tablename__ = "bot_versions"
    
    bot_id = Column(UUID, ForeignKey("bots.id"), nullable=False, index=True)
    version_number = Column(String(10), nullable=False)
    code = Column(Text, nullable=False)
    config = Column(Text, nullable=True)
    created_by = Column(UUID, ForeignKey("users.id"), nullable=False)
    changes_description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=False, index=True)
    
    # Relationships
    bot = relationship("Bot", back_populates="versions")
    
    def __repr__(self) -> str:
        return f"<BotVersion(bot_id={self.bot_id}, version={self.version_number})>"

class BotExecution(Base, UUIDMixin, TimestampMixin):
    """Record of bot executions"""
    __tablename__ = "bot_executions"
    
    bot_id = Column(UUID, ForeignKey("bots.id"), nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="running", index=True)  # running, success, failed
    result = Column(Text, nullable=True)  # JSON as string
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    
    # Relationships
    bot = relationship("Bot", back_populates="executions")
    
    def __repr__(self) -> str:
        return f"<BotExecution(bot_id={self.bot_id}, status={self.status})>"
```

**Test:**
```bash
python -c "
from app.models.bot import Bot, BotVersion, BotExecution
print('✅ All bot models created successfully')
"
```

---

## 🗂️ TUESDAY MORNING: AUDIT LOGGING

### Task 4: Create Audit Model (30 min)

**Create file: `app/models/audit_log.py`**

```python
"""Audit logging models"""

from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, UUID, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, UUIDMixin

class AuditLog(Base, UUIDMixin):
    """Audit trail for compliance and debugging"""
    __tablename__ = "audit_logs"
    
    user_id = Column(UUID, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)  # CREATE_BOT, DELETE_BOT, etc
    resource_type = Column(String(50), nullable=False, index=True)  # BOT, USER, etc
    resource_id = Column(UUID, nullable=True, index=True)
    changes = Column(Text, nullable=True)  # JSON of what changed
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    status = Column(String(50), default="success")  # success, failure
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self) -> str:
        return f"<AuditLog(action={self.action}, resource_id={self.resource_id})>"
```

---

## 🔧 TUESDAY AFTERNOON: ALEMBIC MIGRATIONS

### Task 5: Set Up Alembic (45 min)

```bash
# Initialize Alembic
alembic init migrations

# Edit migrations/alembic.ini
# Change: sqlalchemy.url = driver://user:password@localhost/dbname
# To: sqlalchemy.url = postgresql://localhost/codex32_dev

# Edit migrations/env.py
# Import your models:
# from app.models.base import Base
# from app.models.user import User
# from app.models.bot import Bot, BotVersion, BotExecution
# from app.models.audit_log import AuditLog

# Set target_metadata:
# target_metadata = Base.metadata

# Create initial migration
alembic revision --autogenerate -m "001_initial_schema"

# Apply migration
alembic upgrade head

# Verify
psql codex32_dev -c "\dt"  # List tables
```

**Expected output:**
```
Schema |       Name        | Type  | Owner
--------+-------------------+-------+-------
public | alembic_version   | table | user
public | users             | table | user
public | bots              | table | user
public | bot_versions      | table | user
public | bot_executions    | table | user
public | audit_logs        | table | user
public | api_keys          | table | user
```

---

## 📊 WEDNESDAY: DATA MIGRATION

### Task 6: Create Migration Script (1 hour)

**Create file: `scripts/migrate_json_to_db.py`**

```python
#!/usr/bin/env python3
"""Migrate existing JSON bot data to PostgreSQL"""

import json
import sys
from pathlib import Path
from datetime import datetime
from uuid import uuid4
import os
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.base import SessionLocal, init_db
from app.models.user import User, UserRole
from app.models.bot import Bot

def main():
    print("🚀 Starting JSON to PostgreSQL migration...")
    
    # Initialize database tables
    init_db()
    print("✅ Database tables created")
    
    session = SessionLocal()
    
    try:
        # Create default user
        default_user = session.query(User).filter_by(email="admin@local").first()
        if not default_user:
            default_user = User(
                email="admin@local",
                username="admin",
                hashed_password="$$2b$$12$$placeholder",
                role=UserRole.ADMIN,
                is_active=True
            )
            session.add(default_user)
            session.flush()
            print("✅ Created default admin user")
        
        # Load existing bot registry
        registry_path = Path("codex32_registry.json")
        if not registry_path.exists():
            print("⚠️  No existing bots to migrate")
            session.commit()
            return
        
        with open(registry_path) as f:
            registry = json.load(f)
        
        print(f"📝 Found {len(registry)} bots to migrate")
        
        # Migrate each bot
        migrated_count = 0
        for bot_name, bot_meta in registry.items():
            # Load bot code
            bot_file = Path(f"bots/{bot_name}/bot.py")
            if not bot_file.exists():
                print(f"⚠️  Bot file not found: {bot_file}")
                continue
            
            with open(bot_file) as f:
                code = f.read()
            
            # Create bot record
            bot = Bot(
                name=bot_name,
                description=bot_meta.get("description", ""),
                code=code,
                owner_id=default_user.id,
                status="inactive"
            )
            session.add(bot)
            migrated_count += 1
            print(f"  ✅ {bot_name}")
        
        session.commit()
        print(f"\n✅ Migration complete! Migrated {migrated_count} bots")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    main()
```

**Run migration:**
```bash
python scripts/migrate_json_to_db.py
```

**Verify:**
```bash
python -c "
from app.models.base import SessionLocal
from app.models.bot import Bot

session = SessionLocal()
bots = session.query(Bot).all()
print(f'✅ Database contains {len(bots)} bots')
for bot in bots:
    print(f'  - {bot.name}')
session.close()
"
```

---

## 🧪 THURSDAY: TESTING & BACKUPS

### Task 7: Create Tests (1 hour)

**Create file: `tests/test_database.py`**

```python
"""Database tests"""

import pytest
from app.models.base import SessionLocal, init_db, Base, engine
from app.models.user import User, UserRole
from app.models.bot import Bot

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create tables for testing"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db():
    """Database session for tests"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

def test_create_user(db):
    """Test creating a user"""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed",
        role=UserRole.USER
    )
    db.add(user)
    db.commit()
    
    retrieved = db.query(User).filter_by(email="test@example.com").first()
    assert retrieved is not None
    assert retrieved.username == "testuser"

def test_create_bot(db):
    """Test creating a bot"""
    user = User(
        email="bot-owner@example.com",
        username="botowner",
        hashed_password="hashed",
        role=UserRole.USER
    )
    db.add(user)
    db.flush()
    
    bot = Bot(
        name="test_bot",
        description="Test bot",
        code="print('hello')",
        owner_id=user.id
    )
    db.add(bot)
    db.commit()
    
    retrieved = db.query(Bot).filter_by(name="test_bot").first()
    assert retrieved is not None
    assert retrieved.owner_id == user.id

def test_database_connection(db):
    """Test database is accessible"""
    result = db.execute("SELECT 1")
    assert result.scalar() == 1
```

**Run tests:**
```bash
pytest tests/test_database.py -v
```

### Task 8: Backup Strategy (30 min)

```bash
# Create backups directory
mkdir -p backups

# Manual backup
pg_dump codex32_dev > backups/codex32_backup_$(date +%Y%m%d_%H%M%S).sql

# Create backup script
cat > scripts/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="backups"
mkdir -p $BACKUP_DIR
FILENAME="$BACKUP_DIR/codex32_$(date +%Y%m%d_%H%M%S).sql"
pg_dump codex32_dev > $FILENAME
echo "✅ Backup created: $FILENAME"
gzip $FILENAME  # Compress it
EOF

chmod +x scripts/backup.sh

# Run backup
./scripts/backup.sh
```

---

## 📈 FRIDAY: PERFORMANCE BASELINE & REVIEW

### Task 9: Performance Testing (1 hour)

**Create file: `scripts/benchmark_baseline.py`**

```python
#!/usr/bin/env python3
"""Baseline performance measurements"""

import time
import json
from app.models.base import SessionLocal
from app.models.bot import Bot, BotExecution
from datetime import datetime

def benchmark_query_time():
    """Measure query performance"""
    session = SessionLocal()
    
    # Warm up
    session.query(Bot).all()
    
    # Measure
    start = time.time()
    bots = session.query(Bot).all()
    duration = (time.time() - start) * 1000
    
    session.close()
    
    print(f"Query time (get all bots): {duration:.2f}ms")
    assert duration < 100, f"Query too slow: {duration}ms"

def benchmark_create_bot():
    """Measure bot creation time"""
    session = SessionLocal()
    
    start = time.time()
    from app.models.user import User
    user = session.query(User).first()
    
    bot = Bot(
        name=f"perf_test_{int(time.time())}",
        code="test code",
        owner_id=user.id
    )
    session.add(bot)
    session.commit()
    duration = (time.time() - start) * 1000
    
    session.close()
    
    print(f"Bot creation time: {duration:.2f}ms")
    assert duration < 200, f"Creation too slow: {duration}ms"

def save_baseline():
    """Save performance baseline"""
    baseline = {
        "timestamp": datetime.utcnow().isoformat(),
        "query_time_ms": "<100",
        "creation_time_ms": "<200",
        "target_response_time_ms": "<100"
    }
    
    with open("performance_baseline.json", "w") as f:
        json.dump(baseline, f, indent=2)
    
    print("✅ Performance baseline saved")

if __name__ == "__main__":
    print("🏃 Running performance baseline...")
    benchmark_query_time()
    benchmark_create_bot()
    save_baseline()
    print("✅ Baseline complete!")
```

**Run benchmark:**
```bash
python scripts/benchmark_baseline.py
```

### Task 10: Friday Review

**Checklist:**
- [ ] PostgreSQL running
- [ ] All 7 tables created
- [ ] 0 data loss (all bots migrated)
- [ ] Alembic migrations working
- [ ] Tests passing
- [ ] Backups created
- [ ] Performance baseline set

**If all ✅, Week 1 COMPLETE!**

---

## 🎯 WEEK 1 SUCCESS CRITERIA

```
MUST HAVE (Go/No-Go):
☑ PostgreSQL database running
☑ codex32_dev database with 7 tables
☑ All bot data successfully migrated
☑ Zero data loss (verify in DB)
☑ Alembic migrations set up
☑ Automatic backups working
☑ All tests passing
☑ Performance baseline < 100ms queries

NICE TO HAVE:
☑ Performance optimizations
☑ Additional test coverage
☑ Documentation updated
```

---

## 📋 COMMAND REFERENCE

```bash
# View all tables
psql codex32_dev -c "\dt"

# Check row counts
psql codex32_dev -c "SELECT tablename, COUNT(*) FROM pg_tables WHERE schemaname='public';"

# Query bots
psql codex32_dev -c "SELECT name, status, execution_count FROM bots LIMIT 10;"

# Test Python connection
python -c "from app.models.base import check_database; print('✅ DB OK' if check_database() else '❌ DB Failed')"

# Run all tests
pytest tests/ -v

# Create backup
./scripts/backup.sh

# Apply migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"
```

---

**Week 1 = FOUNDATION COMPLETE** ✅

Next: Week 2 - ORM Integration & API Updates

