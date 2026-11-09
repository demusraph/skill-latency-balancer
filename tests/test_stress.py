import unittest
import asyncio
import sqlite3
import os
import uuid
from fastapi.testclient import TestClient
from src.skill_latency_balancer.core import PIDController, PIDConfig, DatabaseManager, ExecutionScheduler
from src.skill_latency_balancer.web import app

class TestStress(unittest.TestCase):
    def setUp(self):
        self.db_path = f"test_metrics_{uuid.uuid4().hex}.db"

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                pass

    def test_pid_controller_stability(self):
        """Test PID controller output clamping and convergence."""
        config = PIDConfig(kp=0.5, ki=0.1, kd=0.05, target_latency=100.0)
        controller = PIDController(config)
        
        # Test extreme latency spikes
        outputs = [controller.compute(1000.0) for _ in range(10)]
        for out in outputs:
            self.assertTrue(1 <= out <= 100, f"Output {out} out of bounds")
        
        # Test convergence towards target
        final_output = controller.compute(100.0)
        self.assertIsInstance(final_output, int)

    def test_database_throughput(self):
        """Test high-volume SQLite write performance."""
        db = DatabaseManager(db_path=self.db_path)
        iterations = 500
        for i in range(iterations):
            db.log_metric(latency=10.5 + i, limit=50)
        
        with sqlite3.connect(self.db_path) as conn:
            count = conn.execute("SELECT COUNT(*) FROM metrics").fetchone()[0]
            self.assertEqual(count, iterations)

    def test_scheduler_concurrency(self):
        """Test PriorityQueue handling under concurrent load."""
        scheduler = ExecutionScheduler(db_path=self.db_path)
        
        async def producer():
            for i in range(100):
                await scheduler.submit_task({"skill_name": "test", "priority": i % 10})
        
        async def run_test():
            await producer()
            self.assertEqual(scheduler.queue.qsize(), 100)
            
            # Process one to verify priority
            priority, task = await scheduler.queue.get()
            self.assertEqual(priority, -9) # Highest priority (9) becomes -9
            scheduler.queue.task_done()

        asyncio.run(run_test())

    def test_web_dashboard_endpoint(self):
        """Test FastAPI dashboard accessibility."""
        client = TestClient(app)
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Skill Latency Balancer", response.text)

    def test_websocket_lifecycle(self):
        """Test WebSocket connection handshake and data structure."""
        client = TestClient(app)
        with client.websocket_connect("/ws") as websocket:
            data = websocket.receive_json()
            self.assertIsInstance(data, list)
            self.assertTrue(len(data) >= 3)
            # Verify schema of first node
            node = data[0]
            self.assertIn("node_id", node)
            self.assertIn("latency_ms", node)
            self.assertIsInstance(node["latency_ms"], float)

if __name__ == "__main__":
    unittest.main()