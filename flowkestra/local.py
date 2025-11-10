import os
import subprocess
import sys

class LocalTrainer:
    def __init__(self, workdir, venv_name, requirements, mlflow_uri=None):
        self.workdir = workdir
        self.venv_name = venv_name
        self.requirements = requirements
        self.mlflow_uri = mlflow_uri

    def setup_environment(self):
        os.makedirs(self.workdir, exist_ok=True)
        venv_path = os.path.join(self.workdir, self.venv_name)

        if not os.path.exists(venv_path):
            print(f"Creating virtualenv at {venv_path}")
            subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)

        pip_path = os.path.join(venv_path, "bin", "pip")
        subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)
        subprocess.run([pip_path, "install", "-r", self.requirements], check=True)
        print("✅ Local environment ready.")

    def deploy_script(self, script_path):
        print(f"Using local script: {script_path}")
        return script_path

    def deploy_dataset(self, dataset_path):
        print(f"Using local dataset: {dataset_path}")

    def run_training(self, script_path, additional_env=None):
        env = os.environ.copy()
        if self.mlflow_uri:
            env["MLFLOW_TRACKING_URI"] = self.mlflow_uri
        if additional_env:
            env.update(additional_env)

        venv_python = os.path.join(self.workdir, self.venv_name, "bin", "python")
        subprocess.run([venv_python, script_path], check=True, env=env)

    def close(self):
        pass
