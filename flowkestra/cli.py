import argparse
import sys
import subprocess
import os
from flowkestra.manager import TrainingManager

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
        "--async", "-a",
        dest="run_async",               # 👈 use different variable name
        action="store_true",
        help="Run training asynchronously (non-blocking)"
    )

    args = parser.parse_args()

    manager = TrainingManager(args.file)
    manager.setup()

    script_path = manager.config.get("script_path")
    if not script_path:
        print("Error: 'script_path' must be defined in the YAML file")
        sys.exit(1)

    deployed_script = manager.deploy_script(script_path)
    additional_env = manager.config.get("env_vars", {})

    # Run in async mode
    if args.run_async:  # 👈 use run_async instead of async
        env = os.environ.copy()
        env.update(additional_env)

        print("🚀 Launching training in background... MLflow will track it remotely.")
        subprocess.Popen(
            ["python", deployed_script],
            env=env,
            stdout=open("training.log", "w"),
            stderr=subprocess.STDOUT,
            preexec_fn=os.setpgrp  # Detach from CLI
        )
        print("✅ Training started asynchronously. Track progress in MLflow UI.")
        print("Logs are being written to training.log.")
        return

    # Default: blocking mode
    manager.run_training(deployed_script, additional_env)

    artifacts = manager.config.get("artifacts", [])
    for artifact in artifacts:
        manager.download_artifact(artifact["source"], artifact["target"])

    manager.close()
    print("✅ Training finished successfully!")
