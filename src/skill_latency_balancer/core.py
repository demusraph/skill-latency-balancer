import asyncio
import time
import sqlite3
from typing import List
from dataclasses import dataclass

@dataclass
class PIDConfig:
    kp: float = 0.5
    ki: float = 0.1
    kd: float = 0.05
    target_latency: float = 100.0  # ms

class PIDController:
    def __init__(self, config: PIDConfig):
        self.config = config
        self.integral = 0.0
        self.last_error = 0.0
        self.last_time = time.time()

    def compute(self, current_latency: float) -> int:
        now = time.time()
        dt = now - self.last_time
        if dt <= 0: dt = 0.001
        
        error = self.config.target_latency - current_latency
        self.integral += error * dt
        derivative = (error - self.last_error) / dt
        
        output = (self.config.kp * error) + (self.config.ki * self.integral) + (self.config.kd * derivative)
        
        self.last_error = error
        self.last_time = now
        
        return max(1, min(100, int(output + 10)))

class DatabaseManager:
    def __init__(self, db_path: str = "slb_telemetry.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    latency_ms REAL,
                    throttle_limit INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def log_metric(self, latency: float, limit: int):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "INSERT INTO metrics (latency_ms, throttle_limit) VALUES (?, ?)",
                (latency, limit)
            )
            conn.commit()
        finally:
            conn.close()

class ExecutionScheduler:
    def __init__(self, db_path: str = "slb_telemetry.db"):
        self.queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.pid = PIDController(PIDConfig())
        self.db = DatabaseManager(db_path)
        self.current_throttle = 10

    async def submit_task(self, task: dict):
        await self.queue.put((-task.get("priority", 5), task))

    async def run_worker(self):
        while True:
            priority, task = await self.queue.get()
            start = time.perf_counter()
            await asyncio.sleep(0.05) 
            latency = (time.perf_counter() - start) * 1000
            self.current_throttle = self.pid.compute(latency)
            self.db.log_metric(latency, self.current_throttle)
            self.queue.task_done()