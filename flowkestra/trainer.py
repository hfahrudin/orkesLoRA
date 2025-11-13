import os
from flowkestra.runner import Runner
from pathlib import Path
import shutil

class Trainer:
    def __init__(self, name, workdir, origin_dir, requirements, pipelines, mlflow_uri=None, ssh_client=None):
        """
        Args:
            name (str): Experiment name
            workdir (str or Path): local or remote working directory
            origin_dir (str or Path): directory containing scripts and resources
            requirements (str or Path): path to requirements.txt
            pipelines (dict): ordered dict of {step_name: script_name}
            mlflow_uri (str, optional)
            ssh_client (SSHClient, optional): if provided, run on remote server
        """
        self.name = name
        self.origin_dir = Path(origin_dir)
        self.workdir = Path(workdir)
        self.requirements = Path(requirements)
        self.pipelines = pipelines
        self.mlflow_uri = mlflow_uri

        # Initialize Runner (local or remote)
        self.runner = Runner(workdir=self.workdir, ssh_client=ssh_client)

        # Copy all files from origin_dir to workdir
        self._sync_workdir()

        # Setup environment
        self.runner.setup_environment(self.requirements)
        print(f"Environment for {self.name} has been prepared at {self.workdir}")

    def _sync_workdir(self):
        """Copy origin_dir contents to workdir (local or remote)."""
        if self.runner.ssh_client:
            # Remote: use SFTP
            self.runner.ssh_client.open_sftp()
            for src_path in self.origin_dir.glob("**/*"):
                if src_path.is_file():
                    rel_path = src_path.relative_to(self.origin_dir)
                    dest_path = self.workdir / rel_path
                    # Ensure remote directories exist
                    remote_dir = dest_path.parent
                    self.runner.ssh_client.execute(f"mkdir -p {remote_dir}")
                    self.runner.ssh_client.upload(str(src_path), str(dest_path))
        else:
            # Local copy
            self.workdir.mkdir(parents=True, exist_ok=True)
            for src_path in self.origin_dir.glob("**/*"):
                if src_path.is_file():
                    dest_path = self.workdir / src_path.relative_to(self.origin_dir)
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_path, dest_path)

    def run(self):
        """Run all pipeline scripts in sequence with prepared environment."""
        env = os.environ.copy()
        if self.mlflow_uri:
            env["MLFLOW_TRACKING_URI"] = self.mlflow_uri

        results = {}
        for step_name, script_name in self.pipelines.items():
            script_path = self.workdir / script_name  # always run from workdir
            print(f"\n=== Running step: {step_name} ({script_name}) ===")
            result = self.runner.run_script(script_path, additional_env=env)
            results[step_name] = result
        return results
