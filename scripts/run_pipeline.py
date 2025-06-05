#!/usr/bin/env python3
"""
Lancement direct du pipeline Dataflow
Structure simple selon les bonnes pratiques Dataflow
"""

import os
import subprocess
import sys

if __name__ == "__main__":
    # Lance directement le pipeline unifié
    script_path = os.path.join(os.path.dirname(__file__), "..", "src", "dataflow_pipeline_unified.py")
    subprocess.run([sys.executable, script_path] + sys.argv[1:]) 