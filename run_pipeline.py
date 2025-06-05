#!/usr/bin/env python3
"""
Lancement direct du pipeline Dataflow
Structure simple selon les bonnes pratiques Dataflow
"""

import subprocess
import sys

if __name__ == "__main__":
    # Lance directement le pipeline unifié
    subprocess.run([sys.executable, "dataflow_pipeline_unified.py"] + sys.argv[1:]) 