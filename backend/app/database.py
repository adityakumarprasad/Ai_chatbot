from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from backend.app.config import settings

# Global references to connection pool and checkpointer
db_pool = None
checkpointer = None

def get_db_pool() -> AsyncConnectionPool:
    """Get or initialize the PostgreSQL connection pool."""
    global db_pool
    if db_pool is None:
        db_pool = AsyncConnectionPool(
            conninfo=settings.DATABASE_URL,
            max_size=10,
            open=False,  # Do not open synchronously on load
            kwargs={"autocommit": True}
        )
    return db_pool

async def init_checkpointer() -> AsyncPostgresSaver:
    """Initialize the PostgreSQL checkpointer and run database migrations."""
    global checkpointer
    if checkpointer is None:
        pool = get_db_pool()
        # Open pool asynchronously if it's not already open
        await pool.open()
        checkpointer = AsyncPostgresSaver(pool)
        # Sets up the schemas/tables in Postgres for checkpoints
        await checkpointer.setup()
    return checkpointer

async def close_db_pool():
    """Close the database pool on application shutdown."""
    global db_pool
    if db_pool is not None:
        await db_pool.close()
        db_pool = None
