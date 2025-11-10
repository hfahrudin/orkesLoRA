import os
from flowkestra.utils import SSHClient  # your SSH wrapper

class RemoteTrainer:
    def __init__(self, hostname, username, password=None, key_filename=None, port=22,
                 remote_workdir="/home/user/training", venv_name="flowkestra_env",
                 requirements="requirements.txt", mlflow_uri=None):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.port = port
        self.remote_workdir = remote_workdir
        self.venv_name = venv_name
        self.requirements = requirements
        self.mlflow_uri = mlflow_uri
        self.ssh = SSHClient(hostname, username, password, key_filename, port)
        self.ssh.connect()

    def setup_environment(self):
        """Create venv + install deps remotely"""
        print("Setting up remote environment...")
        self.ssh.execute(f"mkdir -p {self.remote_workdir}")
        venv_path = f"{self.remote_workdir}/{self.venv_name}"

        # Create venv
        self.ssh.execute(f"python3 -m venv {venv_path}")

        # Upload requirements.txt
        self.ssh.upload(self.requirements, f"{self.remote_workdir}/requirements.txt")

        # Install dependencies
        self.ssh.execute(f"{venv_path}/bin/pip install --upgrade pip")
        self.ssh.execute(f"{venv_path}/bin/pip install -r {self.remote_workdir}/requirements.txt")

        print("✅ Remote environment ready.")

    def deploy_script(self, script_path):
        filename = os.path.basename(script_path)
        remote_path = f"{self.remote_workdir}/{filename}"
        self.ssh.upload(script_path, remote_path)
        return remote_path

    def deploy_dataset(self, dataset_path):
        remote_dataset = f"{self.remote_workdir}/{os.path.basename(dataset_path)}"
        self.ssh.upload(dataset_path, remote_dataset)
        return remote_dataset

    def run_training(self, script_path, additional_env=None):
        env_vars = f"MLFLOW_TRACKING_URI={self.mlflow_uri}" if self.mlflow_uri else ""
        if additional_env:
            env_vars += " " + " ".join([f"{k}='{v}'" for k, v in additional_env.items()])
        cmd = f"cd {self.remote_workdir} && {env_vars} ./{self.venv_name}/bin/python {script_path}"
        self.ssh.execute(cmd)

    def download_artifact(self, source_path, target_path):
        self.ssh.download(source_path, target_path)

    def close(self):
        self.ssh.close()
