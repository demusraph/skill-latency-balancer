import unittest
import asyncio
import os
import sqlite3
import uuid
from datetime import datetime
from src.skill_latency_balancer.models import TaskRequest, TelemetryMetric, ExecutionResult
from src.skill_latency_balancer.core import PIDConfig, PIDController, DatabaseManager, ExecutionScheduler

class TestCoreComponents(unittest.TestCase):

    def setUp(self):
        self.db_path = f"test_metrics_{uuid.uuid4().hex}.db"

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                pass

    def test_task_request_model(self):
        task = TaskRequest(skill_name="test_skill", payload={"key": "value"})
        self.assertIsInstance(task.task_id, uuid.UUID)
        self.assertEqual(task.priority, 5)
        self.assertEqual(task.skill_name, "test_skill")

    def test_pid_controller_logic(self):
        config = PIDConfig(kp=0.5, ki=0.1, kd=0.05, target_latency=100.0)
        pid = PIDController(config)
        output = pid.compute(50.0)
        self.assertTrue(1 <= output <= 100)
        output_high = pid.compute(200.0)
        self.assertNotEqual(output, output_high)

    def test_database_initialization(self):
        db = DatabaseManager(self.db_path)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='metrics'")
            self.assertIsNotNone(cursor.fetchone())

    def test_database_logging(self):
        db = DatabaseManager(self.db_path)
        db.log_metric(45.5, 20)
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT latency_ms, throttle_limit FROM metrics").fetchone()
            self.assertEqual(row[0], 45.5)
            self.assertEqual(row[1], 20)

    def test_execution_scheduler_queue_ordering(self):
        scheduler = ExecutionScheduler(self.db_path)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(scheduler.submit_task({"priority": 1, "id": "low"}))
        loop.run_until_complete(scheduler.submit_task({"priority": 10, "id": "high"}))
        priority, task = loop.run_until_complete(scheduler.queue.get())
        self.assertEqual(task["id"], "high")
        self.assertEqual(priority, -10)
        loop.close()

    def test_telemetry_metric_model(self):
        metric = TelemetryMetric(latency_ms=12.5, queue_depth=5, throttle_limit=50)
        self.assertEqual(metric.latency_ms, 12.5)
        self.assertIsInstance(metric.timestamp, datetime)

    def test_execution_result_model(self):
        tid = uuid.uuid4()
        res = ExecutionResult(task_id=tid, status="success", execution_time_ms=10.0)
        self.assertEqual(res.task_id, tid)
        self.assertIsNone(res.error)

    def test_pid_dt_clamping(self):
        pid = PIDController(PIDConfig())
        pid.last_time = 0 
        output = pid.compute(100.0)
        self.assertIsInstance(output, int)

    def test_scheduler_initial_state(self):
        scheduler = ExecutionScheduler(self.db_path)
        self.assertEqual(scheduler.current_throttle, 10)
        self.assertIsInstance(scheduler.queue, asyncio.PriorityQueue)