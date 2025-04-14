import os
from logging.config import fileConfig
from sqlalchemy import create_engine, pool
from alembic import context
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Import metadata
from app.models.models import Base
target_metadata = Base.metadata

# Alembic config
config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

# Pull raw URL directly from env
db_url = os.getenv("DATABASE_URL")

# Migrations (offline mode)
def run_migrations_offline():
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

# Migrations (online mode)
def run_migrations_online():
    connectable = create_engine(db_url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

# Entry point
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
