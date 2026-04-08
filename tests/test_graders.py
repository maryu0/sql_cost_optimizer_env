"""
Tests for deterministic graders.
Verifies that graders return varying scores between 0.0 and 1.0.
"""
import pytest
from src.graders import IndexAdvisorGrader, QueryRewriterGrader, SchemaNormalizerGrader
from src.utils.db_executor import DatabaseExecutor
from src.utils.seed_data import get_ecommerce_schema, get_ecommerce_seed_data


class TestIndexAdvisorGrader:
    """Test Index Advisor grader determinism and score variation."""

    @pytest.fixture
    def db(self):
        """Create test database."""
        db = DatabaseExecutor()
        db.execute_schema(get_ecommerce_schema())
        db.execute_seed_data(get_ecommerce_seed_data())
        yield db
        db.close()

    def test_perfect_indexes(self, db):
        """Test with all required indexes."""
        grader = IndexAdvisorGrader()
        sql = """
        CREATE INDEX idx_users_country ON users(country);
        CREATE INDEX idx_orders_status ON orders(status);
        CREATE INDEX idx_orders_user_id ON orders(user_id);
        """
        score, feedback = grader.grade(sql, db, 100.0, 30.0)
        
        assert 0.9 <= score <= 1.0, f"Expected high score, got {score}"
        assert "required indexes" in feedback.lower()

    def test_partial_indexes(self, db):
        """Test with only some required indexes."""
        grader = IndexAdvisorGrader()
        sql = "CREATE INDEX idx_users_country ON users(country);"
        score, feedback = grader.grade(sql, db, 100.0, 60.0)
        
        assert 0.2 <= score <= 0.5, f"Expected medium score, got {score}"

    def test_no_indexes(self, db):
        """Test with no valid indexes."""
        grader = IndexAdvisorGrader()
        sql = "SELECT * FROM users;"
        score, feedback = grader.grade(sql, db, 100.0, 100.0)
        
        assert score == 0.0, f"Expected zero score, got {score}"

    def test_wrong_indexes(self, db):
        """Test with wrong indexes."""
        grader = IndexAdvisorGrader()
        sql = "CREATE INDEX idx_products_name ON products(name);"
        score, feedback = grader.grade(sql, db, 100.0, 95.0)
        
        assert 0.0 <= score <= 0.2, f"Expected low score, got {score}"

    def test_over_indexing(self, db):
        """Test penalty for too many indexes."""
        grader = IndexAdvisorGrader()
        sql = """
        CREATE INDEX idx1 ON users(user_id);
        CREATE INDEX idx2 ON users(email);
        CREATE INDEX idx3 ON users(name);
        CREATE INDEX idx4 ON users(country);
        CREATE INDEX idx5 ON orders(status);
        CREATE INDEX idx6 ON orders(user_id);
        """
        score, feedback = grader.grade(sql, db, 100.0, 30.0)
        
        assert "over-indexing" in feedback.lower() or "too many" in feedback.lower()

    def test_determinism(self, db):
        """Test that same input produces same output."""
        grader = IndexAdvisorGrader()
        sql = "CREATE INDEX idx_users_country ON users(country);"
        
        score1, feedback1 = grader.grade(sql, db, 100.0, 60.0)
        score2, feedback2 = grader.grade(sql, db, 100.0, 60.0)
        
        assert score1 == score2, "Grader is not deterministic"
        assert feedback1 == feedback2, "Grader feedback is not deterministic"


class TestQueryRewriterGrader:
    """Test Query Rewriter grader determinism and score variation."""

    def test_perfect_rewrite(self):
        """Test with optimal JOIN-based query."""
        grader = QueryRewriterGrader()
        sql = """
        SELECT p.name, COUNT(oi.id) as order_count
        FROM products p
        LEFT JOIN order_items oi ON p.product_id = oi.product_id
        GROUP BY p.product_id, p.name
        """
        
        original_results = [{"name": "Product 1", "order_count": 5}]
        optimized_results = [{"name": "Product 1", "order_count": 5}]
        
        score, feedback = grader.grade(sql, original_results, optimized_results, 100.0, 25.0)
        
        assert score >= 0.8, f"Expected high score, got {score}"
        assert "join" in feedback.lower()

    def test_still_has_subquery(self):
        """Test with subquery still present."""
        grader = QueryRewriterGrader()
        sql = """
        SELECT name,
            (SELECT COUNT(*) FROM order_items WHERE product_id = p.id)
        FROM products p
        """
        
        original_results = [{"name": "Product 1"}]
        optimized_results = [{"name": "Product 1"}]
        
        score, feedback = grader.grade(sql, original_results, optimized_results, 100.0, 80.0)
        
        assert score <= 0.4, f"Expected low score for subquery, got {score}"

    def test_incorrect_results(self):
        """Test with mismatched results."""
        grader = QueryRewriterGrader()
        sql = "SELECT * FROM products"
        
        original_results = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
        optimized_results = [{"id": 1, "name": "A"}]  # Missing row!
        
        score, feedback = grader.grade(sql, original_results, optimized_results, 100.0, 50.0)
        
        assert score <= 0.5, f"Expected penalty for wrong results, got {score}"
        assert "not match" in feedback.lower() or "critical" in feedback.lower()

    def test_determinism(self):
        """Test determinism."""
        grader = QueryRewriterGrader()
        sql = "SELECT * FROM products"
        results = [{"id": 1}]
        
        score1, _ = grader.grade(sql, results, results, 100.0, 50.0)
        score2, _ = grader.grade(sql, results, results, 100.0, 50.0)
        
        assert score1 == score2, "Grader is not deterministic"


class TestSchemaNormalizerGrader:
    """Test Schema Normalizer grader determinism and score variation."""

    @pytest.fixture
    def db(self):
        """Create test database."""
        db = DatabaseExecutor()
        yield db
        db.close()

    def test_perfect_normalization(self, db):
        """Test with proper normalization."""
        grader = SchemaNormalizerGrader()
        sql = """
        CREATE TABLE locations (
            id INTEGER PRIMARY KEY,
            country TEXT,
            city TEXT
        );
        
        CREATE TABLE devices (
            id INTEGER PRIMARY KEY,
            device_type TEXT
        );
        
        CREATE TABLE events_normalized (
            id INTEGER PRIMARY KEY,
            location_id INTEGER,
            device_id INTEGER,
            FOREIGN KEY (location_id) REFERENCES locations(id),
            FOREIGN KEY (device_id) REFERENCES devices(id)
        );
        
        CREATE INDEX idx_events_location ON events_normalized(location_id);
        
        INSERT INTO locations (country, city) VALUES ('USA', 'NYC');
        """
        
        score, feedback = grader.grade(sql, db)
        
        assert score >= 0.8, f"Expected high score, got {score}"

    def test_no_foreign_keys(self, db):
        """Test without foreign keys."""
        grader = SchemaNormalizerGrader()
        sql = """
        CREATE TABLE locations (id INT, country TEXT);
        CREATE TABLE events (id INT, location_id INT);
        """
        
        score, feedback = grader.grade(sql, db)
        
        assert score <= 0.6, f"Expected penalty for no FK, got {score}"
        assert "foreign key" in feedback.lower()

    def test_no_new_tables(self, db):
        """Test without creating new tables."""
        grader = SchemaNormalizerGrader()
        sql = "SELECT * FROM events;"
        
        score, feedback = grader.grade(sql, db)
        
        assert score <= 0.3, f"Expected low score, got {score}"

    def test_partial_normalization(self, db):
        """Test with partial normalization."""
        grader = SchemaNormalizerGrader()
        sql = """
        CREATE TABLE locations (id INT PRIMARY KEY);
        FOREIGN KEY (id) REFERENCES something(id);
        """
        
        score, feedback = grader.grade(sql, db)
        
        assert 0.3 <= score <= 0.7, f"Expected medium score, got {score}"

    def test_determinism(self, db):
        """Test determinism."""
        grader = SchemaNormalizerGrader()
        sql = "CREATE TABLE test (id INT);"
        
        score1, _ = grader.grade(sql, db)
        score2, _ = grader.grade(sql, db)
        
        assert score1 == score2, "Grader is not deterministic"


def test_all_graders_return_valid_range():
    """Test that all graders return scores in [0.0, 1.0]."""
    # This is a meta-test to ensure range compliance
    db = DatabaseExecutor()
    db.execute_schema(get_ecommerce_schema())
    db.execute_seed_data(get_ecommerce_seed_data())
    
    test_cases = [
        (IndexAdvisorGrader(), "CREATE INDEX idx ON users(email);", [db, 100.0, 50.0]),
        (QueryRewriterGrader(), "SELECT * FROM users", [[], [], 100.0, 50.0]),
        (SchemaNormalizerGrader(), "CREATE TABLE test (id INT);", [db])
    ]
    
    for grader, sql, args in test_cases:
        score, _ = grader.grade(sql, *args)
        assert 0.0 <= score <= 1.0, f"{grader.__class__.__name__} returned invalid score: {score}"
    
    db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
