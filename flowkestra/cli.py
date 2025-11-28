import argparse
import sys
import subprocess
import os
from flowkestra.supervisor import Supervisor

def main():
    parser = argparse.ArgumentParser(
        description="flowkestra: Run local or remote ML training from a YAML config"
    )
    parser.add_argument(
        "-f", "--file",
        required=True,
        help="Path to YAML configuration file"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode: shows all output, disables screen clearing, and preserves work directories."
    )

    args = parser.parse_args()

    config_path = args.file
    
    if args.debug:
        print("--- Debug mode enabled ---")
        supervisor = Supervisor(
            config_path=config_path,
            visualize_progress=True,
            clear_screen_on_update=False,
            clean_workdir_after_run=False,
            suppress_runner_output=False
        )
    else:
        supervisor = Supervisor(config_path=config_path)
    
    supervisor.run_all()