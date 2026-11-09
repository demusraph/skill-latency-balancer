import unittest
import uuid
from datetime import datetime
from pydantic import ValidationError
from src.skill_latency_balancer.models import TaskRequest, TelemetryMetric, ExecutionResult

class TestValidation(unittest.TestCase):
    """Exhaustive validation suite for SLB data models."""

    def test_task_request_valid_creation(self):
        """Test successful instantiation of TaskRequest with valid data."""
        data = {"skill_name": "data_processor", "priority": 7, "payload": {"key": "value"}}
        task = TaskRequest(**data)
        self.assertEqual(task.skill_name, "data_processor")
        self.assertEqual(task.priority, 7)
        self.assertIsInstance(task.task_id, uuid.UUID)

    def test_task_request_priority_out_of_bounds_high(self):
        """Test Pydantic validation for priority > 10."""
        with self.assertRaises(ValidationError):
            TaskRequest(skill_name="test", priority=11, payload={})

    def test_task_request_priority_out_of_bounds_low(self):
        """Test Pydantic validation for priority < 0."""
        with self.assertRaises(ValidationError):
            TaskRequest(skill_name="test", priority=-1, payload={})

    def test_task_request_missing_required_fields(self):
        """Test that missing required fields (skill_name, payload) raises ValidationError."""
        with self.assertRaises(ValidationError):
            TaskRequest()

    def test_telemetry_metric_type_coercion(self):
        """Test that TelemetryMetric correctly coerces numeric types."""
        metric = TelemetryMetric(latency_ms="12.5", queue_depth=5, throttle_limit=10)
        self.assertEqual(metric.latency_ms, 12.5)
        self.assertIsInstance(metric.latency_ms, float)

    def test_telemetry_metric_invalid_types(self):
        """Test that non-numeric strings in numeric fields raise ValidationError."""
        with self.assertRaises(ValidationError):
            TelemetryMetric(latency_ms="invalid", queue_depth=5, throttle_limit=10)

    def test_execution_result_optional_error(self):
        """Test that ExecutionResult handles optional error field correctly."""
        res_success = ExecutionResult(task_id=uuid.uuid4(), status="success", execution_time_ms=10.0)
        self.assertIsNone(res_success.error)
        
        res_fail = ExecutionResult(task_id=uuid.uuid4(), status="failed", execution_time_ms=0.0, error="Timeout")
        self.assertEqual(res_fail.error, "Timeout")

    def test_task_request_strict_mode(self):
        """Test that strict mode prevents implicit type conversion (e.g., int to str)."""
        with self.assertRaises(ValidationError):
            # skill_name expects str, passing int should fail in strict mode
            TaskRequest(skill_name=123, payload={})

    def test_task_request_default_values(self):
        """Test that default factories (uuid, datetime) are correctly populated."""
        task = TaskRequest(skill_name="test", payload={})
        self.assertIsInstance(task.task_id, uuid.UUID)
        self.assertIsInstance(task.created_at, datetime)
        self.assertEqual(task.priority, 5)

    def test_telemetry_metric_missing_fields(self):
        """Test that TelemetryMetric fails if required fields are missing."""
        with self.assertRaises(ValidationError):
            TelemetryMetric(latency_ms=10.0) # Missing queue_depth and throttle_limit