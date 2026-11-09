import unittest
import time
from src.skill_latency_balancer.core import PIDController, PIDConfig

class TestBoundaries(unittest.TestCase):
    """
    Exhaustive boundary testing for the PIDController logic within the 
    skill-latency-balancer system.
    """

    def setUp(self):
        self.config = PIDConfig(kp=0.5, ki=0.1, kd=0.05, target_latency=100.0)
        self.pid = PIDController(self.config)

    def test_extreme_low_latency(self):
        """Test behavior when latency is near zero."""
        output = self.pid.compute(0.0001)
        self.assertTrue(1 <= output <= 100, f"Output {output} out of bounds")

    def test_extreme_high_latency(self):
        """Test behavior when latency is extremely high (spike)."""
        output = self.pid.compute(1000000.0)
        self.assertEqual(output, 1, "High latency should clamp to minimum throttle")

    def test_exact_target_latency(self):
        """Test behavior when latency matches target exactly."""
        output = self.pid.compute(100.0)
        self.assertTrue(1 <= output <= 100)

    def test_negative_latency_input(self):
        """Test system robustness against negative latency values."""
        output = self.pid.compute(-50.0)
        self.assertTrue(1 <= output <= 100)

    def test_identical_consecutive_latencies(self):
        """Test stability with uniform input values."""
        self.pid.compute(50.0)
        time.sleep(0.01)
        output = self.pid.compute(50.0)
        self.assertTrue(1 <= output <= 100)

    def test_throttle_clamping_upper_bound(self):
        """Ensure output never exceeds 100."""
        # Force a massive error to push PID output high
        output = self.pid.compute(-1000.0)
        self.assertLessEqual(output, 100)

    def test_throttle_clamping_lower_bound(self):
        """Ensure output never drops below 1."""
        # Force a massive error to push PID output low
        output = self.pid.compute(5000.0)
        self.assertGreaterEqual(output, 1)

    def test_zero_time_delta_handling(self):
        """Test internal handling of near-zero time deltas."""
        # Manually trigger compute twice rapidly to force dt <= 0 logic
        self.pid.compute(50.0)
        output = self.pid.compute(50.0)
        self.assertTrue(1 <= output <= 100)

    def test_large_integral_accumulation(self):
        """Test behavior after sustained error accumulation."""
        for _ in range(10):
            self.pid.compute(200.0)
        output = self.pid.compute(200.0)
        self.assertTrue(1 <= output <= 100)

    def test_single_element_latency_sequence(self):
        """Test system state after exactly one computation."""
        output = self.pid.compute(75.0)
        self.assertIsInstance(output, int)
        self.assertTrue(1 <= output <= 100)

if __name__ == "__main__":
    unittest.main()