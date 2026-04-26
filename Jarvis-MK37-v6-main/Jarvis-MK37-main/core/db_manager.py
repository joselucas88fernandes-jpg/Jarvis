
import aiosqlite
import logging

DB_PATH = "logs/jarvis_journal.db"

class DatabaseManager:
    """Manages the stateful journal database (SQLite)."""
    def __init__(self, db_path=DB_PATH):
        self._db_path = db_path
        self._conn = None

    async def connect(self):
        try:
            self._conn = await aiosqlite.connect(self._db_path)
            await self._conn.row_factory = aiosqlite.Row
            await self._create_tables()
            logging.info("DB: Stateful Journal connected.")
        except Exception as e:
            logging.error(f"DB: Failed to connect to database: {e}")
            raise

    async def disconnect(self):
        if self._conn:
            await self._conn.close()
            logging.info("DB: Stateful Journal disconnected.")

    async def _create_tables(self):
        # Main table for agent tasks/goals
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING', -- PENDING, IN_PROGRESS, SUCCESS, FAILED, HUMAN_INTERVENTION
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        # Table for logging each step (blueprint, code, test result)
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                step_type TEXT NOT NULL, -- BLUEPRINT, GENERATE_CODE, SANDBOX_TEST
                content TEXT,
                result TEXT, -- PASS, FAIL
                entropy_ratio REAL, -- For generated code
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        """)
        await self._conn.commit()

    async def create_task(self, goal: str) -> int:
        cursor = await self._conn.execute(
            "INSERT INTO tasks (goal, status) VALUES (?, ?)", (goal, 'IN_PROGRESS')
        )
        await self._conn.commit()
        return cursor.lastrowid

    async def log_step(self, task_id: int, step_type: str, content: str = None, result: str = None, entropy_ratio: float = None):
        await self._conn.execute(
            "INSERT INTO steps (task_id, step_type, content, result, entropy_ratio) VALUES (?, ?, ?, ?, ?)",
            (task_id, step_type, content, result, entropy_ratio)
        )
        await self._conn.commit()

    async def update_task_status(self, task_id: int, status: str):
        await self._conn.execute(
            "UPDATE tasks SET status = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, task_id)
        )
        await self._conn.commit()

    async def get_unfinished_tasks(self):
        async with self._conn.execute("SELECT * FROM tasks WHERE status = 'IN_PROGRESS'") as cursor:
            return await cursor.fetchall()

    async def get_recent_failures_for_task(self, task_id: int, limit: int = 5):
        query = """
            SELECT content, entropy_ratio FROM steps
            WHERE task_id = ? AND step_type = 'GENERATE_CODE' AND result = 'FAIL'
            ORDER BY created_at DESC LIMIT ?
        """
        async with self._conn.execute(query, (task_id, limit)) as cursor:
            return await cursor.fetchall()
