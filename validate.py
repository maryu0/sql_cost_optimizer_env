"""
Pre-submission validation script for SQL Cost Optimizer Environment.
Checks all hackathon requirements before submission.
"""
import os
import sys
import subprocess
from pathlib import Path


class ValidationResult:
    """Store validation results."""
    
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def add_pass(self, message):
        self.passed.append(f"✅ {message}")
    
    def add_fail(self, message):
        self.failed.append(f"❌ {message}")
    
    def add_warning(self, message):
        self.warnings.append(f"⚠️  {message}")
    
    def print_summary(self):
        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)
        
        if self.passed:
            print(f"\n✅ PASSED ({len(self.passed)}):")
            for msg in self.passed:
                print(f"   {msg}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for msg in self.warnings:
                print(f"   {msg}")
        
        if self.failed:
            print(f"\n❌ FAILED ({len(self.failed)}):")
            for msg in self.failed:
                print(f"   {msg}")
        
        print("\n" + "="*80)
        
        if self.failed:
            print("❌ VALIDATION FAILED - Fix issues before submission!")
            return False
        elif self.warnings:
            print("⚠️  VALIDATION PASSED WITH WARNINGS - Review before submission")
            return True
        else:
            print("✅ VALIDATION PASSED - Ready for submission!")
            return True


def check_file_structure(result: ValidationResult):
    """Check required files exist."""
    print("\n📁 Checking file structure...")
    
    required_files = [
        "openenv.yaml",
        "requirements.txt",
        "Dockerfile",
        ".dockerignore",
        ".env.example",
        ".gitignore",
        "README.md",
        "inference.py",  # CRITICAL: Must be in root
        "src/__init__.py",
        "src/models.py",
        "src/environment.py",
        "src/graders.py",
        "src/rewards.py",
        "src/main.py",
        "src/tasks/__init__.py",
        "src/tasks/task1_index_advisor.py",
        "src/tasks/task2_query_rewriter.py",
        "src/tasks/task3_schema_normalizer.py",
        "src/utils/__init__.py",
        "src/utils/db_executor.py",
        "src/utils/cost_calculator.py",
        "src/utils/seed_data.py",
        "tests/__init__.py",
        "tests/test_graders.py",
        "tests/test_environment.py",
        "tests/test_rewards.py",
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            result.add_pass(f"Found {file_path}")
        else:
            result.add_fail(f"Missing required file: {file_path}")
    
    # Check inference.py is in root (CRITICAL)
    if os.path.exists("inference.py"):
        result.add_pass("inference.py correctly placed in ROOT directory")
    else:
        result.add_fail("CRITICAL: inference.py must be in root directory!")


def check_environment_variables(result: ValidationResult):
    """Check .env.example has required variables."""
    print("\n🔑 Checking environment variables...")
    
    required_vars = [
        "API_BASE_URL",
        "MODEL_NAME",
        "OPENAI_API_KEY",
        "HF_TOKEN"
    ]
    
    if os.path.exists(".env.example"):
        with open(".env.example", "r") as f:
            content = f.read()
        
        for var in required_vars:
            if var in content:
                result.add_pass(f"Found {var} in .env.example")
            else:
                result.add_fail(f"Missing {var} in .env.example")
    else:
        result.add_fail(".env.example not found")


def check_openenv_yaml(result: ValidationResult):
    """Check openenv.yaml structure."""
    print("\n📄 Checking openenv.yaml...")
    
    if os.path.exists("openenv.yaml"):
        with open("openenv.yaml", "r") as f:
            content = f.read()
        
        required_fields = [
            "name: sql-cost-optimizer-env",
            "version:",
            "description:",
            "tasks:",
            "index-advisor",
            "query-rewriter",
            "schema-normalizer",
            "observation_space:",
            "action_space:",
        ]
        
        for field in required_fields:
            if field in content:
                result.add_pass(f"Found '{field}' in openenv.yaml")
            else:
                result.add_warning(f"Missing or different: '{field}' in openenv.yaml")
    else:
        result.add_fail("openenv.yaml not found")


def check_python_imports(result: ValidationResult):
    """Check that Python modules can be imported."""
    print("\n🐍 Checking Python imports...")
    
    try:
        sys.path.insert(0, os.getcwd())
        
        from src.models import Observation, Action, Reward
        result.add_pass("Successfully imported src.models")
        
        from src.environment import SQLOptimizerEnv
        result.add_pass("Successfully imported src.environment")
        
        from src.graders import get_grader
        result.add_pass("Successfully imported src.graders")
        
        from src.rewards import RewardCalculator
        result.add_pass("Successfully imported src.rewards")
        
    except ImportError as e:
        result.add_fail(f"Import error: {e}")


def check_inference_script(result: ValidationResult):
    """Check inference.py structure."""
    print("\n🤖 Checking inference.py...")
    
    if os.path.exists("inference.py"):
        with open("inference.py", "r") as f:
            content = f.read()
        
        # Check for OpenAI client usage (REQUIRED)
        if "from openai import OpenAI" in content or "import openai" in content:
            result.add_pass("Uses OpenAI client (REQUIRED)")
        else:
            result.add_fail("CRITICAL: Must use OpenAI client for LLM calls!")
        
        # Check for environment variable usage
        if "API_BASE_URL" in content and "MODEL_NAME" in content:
            result.add_pass("Reads API_BASE_URL and MODEL_NAME from env")
        else:
            result.add_warning("Should read API_BASE_URL and MODEL_NAME")
        
        # Check for main execution
        if 'if __name__ == "__main__"' in content:
            result.add_pass("Has main execution block")
        else:
            result.add_warning("Should have main execution block")
        
    else:
        result.add_fail("inference.py not found in root directory")


def check_readme_quality(result: ValidationResult):
    """Check README.md completeness."""
    print("\n📖 Checking README.md...")
    
    if os.path.exists("README.md"):
        with open("README.md", "r") as f:
            content = f.read().lower()
        
        required_sections = [
            "overview",
            "quick start",
            "installation",
            "tasks",
            "evaluation criteria",
            "api",
            "docker",
        ]
        
        found_sections = sum(1 for section in required_sections if section in content)
        
        if found_sections >= 5:
            result.add_pass(f"README has {found_sections}/{len(required_sections)} recommended sections")
        else:
            result.add_warning(f"README only has {found_sections}/{len(required_sections)} sections")
        
        # Check word count (should be comprehensive)
        word_count = len(content.split())
        if word_count >= 1000:
            result.add_pass(f"README is comprehensive ({word_count} words)")
        else:
            result.add_warning(f"README is short ({word_count} words) - consider expanding")
    else:
        result.add_fail("README.md not found")


def check_dockerfile(result: ValidationResult):
    """Check Dockerfile quality."""
    print("\n🐳 Checking Dockerfile...")
    
    if os.path.exists("Dockerfile"):
        with open("Dockerfile", "r") as f:
            content = f.read()
        
        required_elements = [
            ("FROM python", "Base image specified"),
            ("WORKDIR", "Working directory set"),
            ("COPY requirements.txt", "Requirements copied"),
            ("RUN pip install", "Dependencies installed"),
            ("EXPOSE", "Port exposed"),
            ("CMD", "Start command specified"),
        ]
        
        for element, description in required_elements:
            if element in content:
                result.add_pass(description)
            else:
                result.add_warning(f"Missing in Dockerfile: {description}")
    else:
        result.add_fail("Dockerfile not found")


def check_task_count(result: ValidationResult):
    """Check that there are 3+ tasks."""
    print("\n🎯 Checking task count...")
    
    task_files = [
        "src/tasks/task1_index_advisor.py",
        "src/tasks/task2_query_rewriter.py",
        "src/tasks/task3_schema_normalizer.py",
    ]
    
    task_count = sum(1 for f in task_files if os.path.exists(f))
    
    if task_count >= 3:
        result.add_pass(f"Has {task_count} tasks (requirement: 3+)")
    else:
        result.add_fail(f"Only {task_count} tasks found (requirement: 3+)")


def check_test_coverage(result: ValidationResult):
    """Check test file existence."""
    print("\n🧪 Checking test coverage...")
    
    test_files = [
        "tests/test_graders.py",
        "tests/test_environment.py",
        "tests/test_rewards.py",
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            result.add_pass(f"Found {test_file}")
        else:
            result.add_warning(f"Missing test file: {test_file}")


def print_pre_submission_checklist(result: ValidationResult):
    """Print the hackathon pre-submission checklist."""
    print("\n" + "="*80)
    print("PRE-SUBMISSION CHECKLIST (MANUAL VERIFICATION REQUIRED)")
    print("="*80)
    
    checklist = [
        "[ ] HF Space deploys - Automated ping returns 200",
        "[ ] OpenEnv spec compliance - Run 'openenv validate .'",
        "[ ] Dockerfile builds - Run 'docker build -t env .'",
        "[ ] Baseline reproduces - Run 'python inference.py'",
        "[ ] 3+ tasks with graders - Verified above",
        "[ ] Environment variables defined - Verified above",
        "[ ] Inference script in root - Verified above",
        "[ ] Uses OpenAI client - Verified above",
        "[ ] Runtime < 20 minutes - Test with 'python inference.py'",
        "[ ] Runs on 2 vCPU / 8GB RAM - Test deployment",
        "[ ] Run validator - 'openenv validate'",
    ]
    
    for item in checklist:
        print(f"   {item}")
    
    print("\n💡 Next Steps:")
    print("   1. Fix any failed validations above")
    print("   2. Run: openenv validate .")
    print("   3. Run: docker build -t sql-cost-optimizer-env .")
    print("   4. Run: python inference.py")
    print("   5. Deploy to Hugging Face Spaces")
    print("   6. Test deployed Space at: https://your-space.hf.space/health")
    print("="*80)


def main():
    """Run all validation checks."""
    print("="*80)
    print("SQL COST OPTIMIZER - PRE-SUBMISSION VALIDATION")
    print("="*80)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    result = ValidationResult()
    
    # Run all checks
    check_file_structure(result)
    check_environment_variables(result)
    check_openenv_yaml(result)
    check_python_imports(result)
    check_inference_script(result)
    check_readme_quality(result)
    check_dockerfile(result)
    check_task_count(result)
    check_test_coverage(result)
    
    # Print results
    result.print_summary()
    print_pre_submission_checklist(result)
    
    # Return exit code
    return 0 if not result.failed else 1


if __name__ == "__main__":
    sys.exit(main())
