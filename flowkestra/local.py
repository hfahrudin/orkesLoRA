import os
import subprocess
import sys
import shutil

class LocalTrainer:
    def __init__(self, target_workdir, venv_name, requirements, mlflow_uri=None, workdir=None):
        self.workdir = workdir
        self.target_workdir = target_workdir
        self.venv_name = venv_name
        self.requirements = requirements
        self.mlflow_uri = mlflow_uri

    def setup_environment(self):
        if self.workdir:
            if os.path.exists(self.target_workdir):
                shutil.rmtree(self.target_workdir)
            shutil.copytree(self.workdir, self.target_workdir)
        else:
            os.makedirs(self.target_workdir, exist_ok=True)
        venv_path = os.path.join(self.target_workdir, self.venv_name)

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

    def run_training(self, script_path, additional_env=None, async_run=False):
        env = os.environ.copy()
        if self.mlflow_uri:
            env["MLFLOW_TRACKING_URI"] = self.mlflow_uri
        if additional_env:
            env.update(additional_env)

        venv_python = os.path.join(self.target_workdir, self.venv_name, "bin", "python")

        if async_run:
            log_file = os.path.basename(script_path) + ".log"
            print(f"🚀 Launching training in background... Logs are being written to {log_file}.")
            subprocess.Popen(
                [venv_python, script_path],
                env=env,
                stdout=open(log_file, "w"),
                stderr=subprocess.STDOUT,
                preexec_fn=os.setpgrp,  # Detach from CLI
                cwd=self.target_workdir
            )
        else:
            try:
                print([venv_python, script_path])
                subprocess.run([venv_python, script_path], check=True, env=env, cwd=self.target_workdir)
            except subprocess.CalledProcessError as e:
                print("Script failed with return code:", e.returncode)
                raise

    def download_artifact(self, source, target):
        source_path = os.path.join(self.target_workdir, source)
        shutil.copytree(source_path, target)

    def close(self):
        pass
