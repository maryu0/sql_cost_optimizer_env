"""
Tests for OpenEnv spec compliance.
Verifies reset(), step(), state() signatures and behavior.
"""
import pytest
from src.environment import SQLOptimizerEnv
from src.models import Action, Observation, Reward


class TestEnvironmentCompliance:
    """Test OpenEnv specification compliance."""

    @pytest.fixture
    def env(self):
        """Create environment instance."""
        env = SQLOptimizerEnv()
        yield env
        env.close()

    def test_reset_returns_observation(self, env):
        """Test that reset() returns an Observation."""
        obs = env.reset()
        
        assert isinstance(obs, Observation)
        assert obs.task_type in ["index-advisor", "query-rewriter", "schema-normalizer"]
        assert len(obs.query) > 0
        assert len(obs.schema) > 0
        assert obs.current_execution_time_ms > 0

    def test_reset_with_task_name(self, env):
        """Test reset() with specific task."""
        obs = env.reset(task_name="index-advisor")
        
        assert obs.task_type == "index-advisor"
        assert env.current_task == "index-advisor"

    def test_reset_with_seed(self, env):
        """Test reset() with seed for reproducibility."""
        obs1 = env.reset(task_name="index-advisor", seed=42)
        env.close()
        
        env2 = SQLOptimizerEnv()
        obs2 = env2.reset(task_name="index-advisor", seed=42)
        
        assert obs1.query == obs2.query
        assert obs1.current_execution_time_ms == obs2.current_execution_time_ms
        env2.close()

    def test_reset_invalid_task_raises(self, env):
        """Test that invalid task name raises ValueError."""
        with pytest.raises(ValueError):
            env.reset(task_name="invalid-task")

    def test_step_signature(self, env):
        """Test that step() returns (obs, reward, done, info)."""
        env.reset(task_name="index-advisor")
        
        action = Action(
            optimized_query="CREATE INDEX idx_test ON users(email);",
            explanation="Test index",
            suggested_changes=["Test"],
            confidence=0.5
        )
        
        result = env.step(action)
        
        assert len(result) == 4, "step() must return 4 values"
        obs, reward, done, info = result
        
        assert isinstance(obs, Observation)
        assert isinstance(reward, Reward)
        assert isinstance(done, bool)
        assert isinstance(info, dict)

    def test_reward_range(self, env):
        """Test that rewards are in [-1.0, 1.0]."""
        env.reset(task_name="index-advisor")
        
        action = Action(
            optimized_query="CREATE INDEX idx_users_country ON users(country);",
            explanation="Index on country",
            suggested_changes=["Added index"],
            confidence=0.8
        )
        
        _, reward, _, _ = env.step(action)
        
        assert -1.0 <= reward.score <= 1.0, f"Reward {reward.score} outside range"

    def test_reward_breakdown(self, env):
        """Test that reward has detailed breakdown."""
        env.reset(task_name="index-advisor")
        
        action = Action(
            optimized_query="CREATE INDEX idx_test ON users(email);",
            explanation="Test",
            suggested_changes=[],
            confidence=0.5
        )
        
        _, reward, _, _ = env.step(action)
        
        assert hasattr(reward, 'breakdown')
        assert hasattr(reward.breakdown, 'grade_score')
        assert hasattr(reward.breakdown, 'performance_improvement')
        assert hasattr(reward.breakdown, 'cost_savings_bonus')

    def test_state_returns_dict(self, env):
        """Test that state() returns a dictionary."""
        env.reset(task_name="index-advisor")
        
        state = env.state()
        
        assert isinstance(state, dict)
        assert 'current_task' in state
        assert 'episode_step' in state
        assert 'cumulative_reward' in state
        assert 'is_done' in state

    def test_episode_termination(self, env):
        """Test that episode terminates correctly."""
        env.reset(task_name="index-advisor")
        
        action = Action(
            optimized_query="SELECT 'bad sql';",
            explanation="Bad action",
            suggested_changes=[],
            confidence=0.0
        )
        
        # Bad action should eventually terminate
        done = False
        max_steps = 10
        step_count = 0
        
        while not done and step_count < max_steps:
            _, _, done, _ = env.step(action)
            step_count += 1
        
        assert step_count <= 5, "Episode should terminate within 5 steps"

    def test_multiple_episodes(self, env):
        """Test multiple reset/step cycles."""
        for i in range(3):
            obs = env.reset(task_name="index-advisor", seed=i)
            assert obs.task_type == "index-advisor"
            assert env.episode_step == 0
            
            action = Action(
                optimized_query="CREATE INDEX idx ON users(email);",
                explanation="Test",
                suggested_changes=[],
                confidence=0.5
            )
            
            env.step(action)
            assert env.episode_step == 1

    def test_action_history_tracking(self, env):
        """Test that action history is tracked."""
        env.reset(task_name="index-advisor")
        
        actions = [
            "CREATE INDEX idx1 ON users(email);",
            "CREATE INDEX idx2 ON users(country);"
        ]
        
        for sql in actions:
            action = Action(
                optimized_query=sql,
                explanation="Test",
                suggested_changes=[],
                confidence=0.5
            )
            env.step(action)
        
        state = env.state()
        assert len(state['action_history']) == 2
        assert state['action_history'][0] == actions[0]

    def test_close_cleanup(self, env):
        """Test that close() cleans up resources."""
        env.reset(task_name="index-advisor")
        env.close()
        
        assert env.db is None

    def test_observation_metadata(self, env):
        """Test that observation includes metadata."""
        obs = env.reset(task_name="index-advisor")
        
        assert 'metadata' in obs.model_dump()
        assert isinstance(obs.metadata, dict)
        assert 'table_info' in obs.metadata
        assert 'baseline_cost_usd' in obs.metadata

    def test_info_dict_content(self, env):
        """Test that info dict contains expected keys."""
        env.reset(task_name="index-advisor")
        
        action = Action(
            optimized_query="CREATE INDEX idx ON users(email);",
            explanation="Test",
            suggested_changes=[],
            confidence=0.5
        )
        
        _, _, _, info = env.step(action)
        
        expected_keys = ['grade_score', 'grade_feedback', 'baseline_time_ms', 
                        'optimized_time_ms', 'cost_report']
        
        for key in expected_keys:
            assert key in info, f"Missing key: {key}"


def test_all_tasks_loadable():
    """Test that all tasks can be loaded."""
    env = SQLOptimizerEnv()
    
    tasks = ["index-advisor", "query-rewriter", "schema-normalizer"]
    
    for task in tasks:
        obs = env.reset(task_name=task)
        assert obs.task_type == task
        assert len(obs.query) > 0
        assert len(obs.schema) > 0
    
    env.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
