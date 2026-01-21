import sys
import os
import importlib
import importlib.util

# Add the current directory to sys.path so we can import pipeline
sys.path.append(os.getcwd())

module_name = "pipeline.pipeline"

try:
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        raise ImportError(f"No module named '{module_name}'")

    module = importlib.import_module(module_name)
    if not hasattr(module, "run_pipeline"):
        raise ImportError(f"'{module_name}' does not define 'run_pipeline'")

    print("Import successful")
except ImportError as e:
    print(f"Import failed: {e}")
except Exception as e:
    print(f"An error occurred: {e}")