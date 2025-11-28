import os
from flowkestra.runner import Runner
from pathlib import Path
import shutil
from flowkestra.utils import SSHClient
from flowkestra.schema import SSHConfig
from typing import Optional

class Worker:
    def __init__(self, worker_id, workdir, origin_dir, main_states, requirements, pipelines, experiment_name=None ,mlflow_uri=None, ssh_config: Optional[SSHConfig] = None, suppress_output=True, clean_workdir_after_run=True):

        self.worker_id = worker_id
        self.origin_dir = Path(origin_dir)
        self.workdir = Path(workdir)
        self.requirements = self.workdir / requirements
        self.pipelines = pipelines
        self.mlflow_uri = mlflow_uri if mlflow_uri else "http://localhost:5000"
        self.experiment_name = experiment_name if experiment_name else "default_experiment"
        self.main_states = main_states
        self.clean_workdir_after_run = clean_workdir_after_run
        if ssh_config:
            self.ssh_client = SSHClient(ssh_config)
        else:
            self.ssh_client = None

        # Initialize Runner (local or remote)
        self.runner = Runner(
            workdir=self.workdir, 
            ssh_client=self.ssh_client,
            suppress_output=suppress_output
        )

        self.main_states[self.worker_id]['status'] = 'synchronizing'
        self._clean_workdir()

        # Now sync origin_dir into the clean directory
        self._sync_workdir()
        self.main_states[self.worker_id]['status'] = 'environment setup'

        # # Setup environment
        self.runner.setup_environment(self.requirements)
        self.main_states[self.worker_id]['status'] = 'ready'
        
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
        additional_env = {
            "MLFLOW_TRACKING_URI": self.mlflow_uri,
            "MLFLOW_EXPERIMENT_NAME": self.experiment_name
        }

        self.main_states[self.worker_id]['status'] = 'training'
        results = {}
        for step_name, pipeline_config in self.pipelines.items():
            script_path = self.workdir / pipeline_config['script']
            script_args = pipeline_config.get('args')
            
            result = self.runner.run_script(
                script_path, 
                args=script_args, 
                additional_env=additional_env
            )
            results[step_name] = result
        
        self.main_states[self.worker_id]['status'] = 'completed'
        if self.clean_workdir_after_run:
            self._clean_workdir()
        return results

    def _clean_workdir(self):
        """Delete all files and subfolders in the workdir (local or remote)."""
        if self.runner.ssh_client:
            # Remote clean
            self.runner.ssh_client.execute(f"rm -rf {self.workdir}/*")
            self.runner.ssh_client.execute(f"rm -rf {self.workdir}/.* 2>/dev/null || true")  
        else:
            # Local clean
            if self.workdir.exists():
                for item in self.workdir.iterdir():
                    if item.is_file():
                        item.unlink()
                    else:
                        shutil.rmtree(item)

    def close(self):
        if self.clean_workdir_after_run:
            self._clean_workdir()