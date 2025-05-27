# This file makes the 'tests' directory a Python package.

import sys
import os

# Add the parent directory (project root) to sys.path
# This allows test files to import modules from data_processing, mcq_generation, and api
# as if the tests were run from the project root.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
