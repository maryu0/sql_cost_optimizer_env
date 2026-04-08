"""
Tests for reward calculation logic.
Verifies that rewards provide varying signals and correct breakdowns.
"""
import pytest
from src.rewards import RewardCalculator


class TestRewardCalculator:
    """Test reward calculation and score variation."""

    @pytest.fixture
    def calculator(self):
        """Create reward calculator instance."""
        return RewardCalculator()

    def test_perfect_optimization(self, calculator):
        """Test reward for perfect optimization."""
        reward = calculator.calculate_reward(
            grade_score=1.0,
            baseline_time_ms=1000.0,
            optimized_time_ms=100.0,  # 10x speedup
            baseline_cost_usd=0.001,
            optimized_cost_usd=0.0001,  # 90% cost reduction
            results_match=True,
            has_errors=False
        )
        
        assert 0.9 <= reward.score <= 1.0, f"Expected high reward, got {reward.score}"
        assert reward.breakdown.grade_score == 1.0
        assert reward.breakdown.performance_improvement == 10.0
        assert reward.breakdown.safety_bonus > 0

    def test_moderate_optimization(self, calculator):
        """Test reward for moderate optimization."""
        reward = calculator.calculate_reward(
            grade_score=0.7,
            baseline_time_ms=1000.0,
            optimized_time_ms=500.0,  # 2x speedup
            baseline_cost_usd=0.001,
            optimized_cost_usd=0.0008,  # 20% cost reduction
            results_match=True,
            has_errors=False
        )
        
        assert 0.5 <= reward.score <= 0.8, f"Expected medium reward, got {reward.score}"

    def test_poor_optimization(self, calculator):
        """Test reward for poor optimization."""
        reward = calculator.calculate_reward(
            grade_score=0.3,
            baseline_time_ms=1000.0,
            optimized_time_ms=1200.0,  # Slower!
            baseline_cost_usd=0.001,
            optimized_cost_usd=0.0015,  # More expensive!
            results_match=True,
            has_errors=False
        )
        
        assert reward.score <= 0.4, f"Expected low reward, got {reward.score}"

    def test_incorrect_results_penalty(self, calculator):
        """Test severe penalty for incorrect results."""
        reward = calculator.calculate_reward(
            grade_score=0.9,
            baseline_time_ms=1000.0,
            optimized_time_ms=100.0,
            baseline_cost_usd=0.001,
            optimized_cost_usd=0.0001,
            results_match=False,  # Wrong results!
            has_errors=False
        )
        
        assert reward.score < 0.5, f"Expected penalty for wrong results, got {reward.score}"
        assert reward.breakdown.correctness_penalty == -0.5

    def test_sql_errors_penalty(self, calculator):
        """Test penalty for SQL execution errors."""
        reward = calculator.calculate_reward(
            grade_score=0.8,
            baseline_time_ms=1000.0,
            optimized_time_ms=100.0,
            baseline_cost_usd=0.001,
            optimized_cost_usd=0.0001,
            results_match=False,
            has_errors=True  # SQL error!
        )
        
        assert reward.score < 0.5, f"Expected penalty for errors, got {reward.score}"

    def test_performance_component_thresholds(self, calculator):
        """Test performance component scoring thresholds."""
        test_cases = [
            (10.0, 0.30),  # 10x speedup → max performance score
            (4.0, 0.27),   # 4x speedup → 90% of max
            (2.5, 0.225),  # 2.5x speedup → 75% of max
            (1.7, 0.15),   # 1.7x speedup → 50% of max
            (1.2, 0.075),  # 1.2x speedup → 25% of max
            (0.8, -0.15),  # 0.8x (slower) → negative
        ]
        
        for speedup, expected_component in test_cases:
            component = calculator._calculate_performance_component(
                baseline_time_ms=1000.0,
                optimized_time_ms=1000.0 / speedup
            )
            
            assert abs(component - expected_component) < 0.01, \
                f"Speedup {speedup}x: expected {expected_component}, got {component}"

    def test_cost_component_thresholds(self, calculator):
        """Test cost component scoring thresholds."""
        test_cases = [
            (0.9, 0.20),   # 90% savings → max cost score
            (0.7, 0.18),   # 70% savings → 90% of max
            (0.5, 0.15),   # 50% savings → 75% of max
            (0.3, 0.10),   # 30% savings → 50% of max
            (0.15, 0.05),  # 15% savings → 25% of max
            (0.05, 0.0),   # 5% savings → no bonus
        ]
        
        baseline = 1.0
        
        for savings_ratio, expected_component in test_cases:
            optimized = baseline * (1 - savings_ratio)
            component = calculator._calculate_cost_component(baseline, optimized)
            
            assert abs(component - expected_component) < 0.01, \
                f"Savings {savings_ratio*100}%: expected {expected_component}, got {component}"

    def test_reward_range_bounds(self, calculator):
        """Test that rewards are always in [-1.0, 1.0]."""
        test_cases = [
            # (grade, baseline_time, opt_time, baseline_cost, opt_cost, match, errors)
            (1.0, 1000, 1, 1.0, 0.001, True, False),      # Best case
            (0.0, 1000, 10000, 0.001, 1.0, False, True),  # Worst case
            (0.5, 1000, 500, 0.001, 0.0005, True, False), # Middle case
        ]
        
        for params in test_cases:
            reward = calculator.calculate_reward(*params)
            assert -1.0 <= reward.score <= 1.0, \
                f"Reward {reward.score} outside bounds for params {params}"

    def test_feedback_generation(self, calculator):
        """Test that feedback is informative."""
        reward = calculator.calculate_reward(
            grade_score=0.9,
            baseline_time_ms=1000.0,
            optimized_time_ms=250.0,
            baseline_cost_usd=0.001,
            optimized_cost_usd=0.0003,
            results_match=True,
            has_errors=False
        )
        
        feedback = reward.feedback.lower()
        
        # Should mention grade
        assert "grade" in feedback or "0.9" in feedback
        
        # Should mention speedup
        assert "faster" in feedback or "speedup" in feedback
        
        # Should mention correctness
        assert "match" in feedback or "correct" in feedback

    def test_done_flag(self, calculator):
        """Test that done flag is set correctly."""
        # High reward should set done=True
        reward_high = calculator.calculate_reward(
            grade_score=0.95,
            baseline_time_ms=1000.0,
            optimized_time_ms=100.0,
            baseline_cost_usd=0.001,
            optimized_cost_usd=0.0001,
            results_match=True,
            has_errors=False
        )
        
        assert reward_high.done is True, "High reward should set done=True"
        
        # Errors should set done=True
        reward_error = calculator.calculate_reward(
            grade_score=0.5,
            baseline_time_ms=1000.0,
            optimized_time_ms=500.0,
            baseline_cost_usd=0.001,
            optimized_cost_usd=0.0005,
            results_match=False,
            has_errors=True
        )
        
        assert reward_error.done is True, "Errors should set done=True"
        
        # Low reward should not set done
        reward_low = calculator.calculate_reward(
            grade_score=0.3,
            baseline_time_ms=1000.0,
            optimized_time_ms=900.0,
            baseline_cost_usd=0.001,
            optimized_cost_usd=0.0009,
            results_match=True,
            has_errors=False
        )
        
        assert reward_low.done is False, "Low reward should not set done=True"

    def test_partial_progress_signals(self, calculator):
        """Test that rewards vary smoothly (not binary)."""
        grades = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        rewards = []
        
        for grade in grades:
            reward = calculator.calculate_reward(
                grade_score=grade,
                baseline_time_ms=1000.0,
                optimized_time_ms=500.0,
                baseline_cost_usd=0.001,
                optimized_cost_usd=0.0005,
                results_match=True,
                has_errors=False
            )
            rewards.append(reward.score)
        
        # Rewards should increase monotonically with grade
        for i in range(len(rewards) - 1):
            assert rewards[i] < rewards[i+1], \
                f"Rewards not increasing: {rewards[i]} >= {rewards[i+1]} for grades {grades[i]}, {grades[i+1]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
