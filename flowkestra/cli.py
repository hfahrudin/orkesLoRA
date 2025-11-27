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

    args = parser.parse_args()

    config_path = args.file
    supervisor = Supervisor(config_path=config_path)
    supervisor.run_all()