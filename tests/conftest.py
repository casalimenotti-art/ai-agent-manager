import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
pytest_plugins = ["tests.test_providers"]  # fixture "server" (LLM finto) condivisa
