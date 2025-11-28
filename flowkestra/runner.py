import os
import sys
import subprocess
from pathlib import Path
import platform

from flowkestra.utils import SSHClient

#ALL MESSAGES PRINTED FROM THIS CLASS SHOULD BE HANDLED BY WORKER HENCE ALL SUPRESSED OUTPUTS
class Runner:
    def __init__(self, workdir, venv_name="venv", ssh_client: SSHClient =None, suppress_output=True):
        """
        Args:
            workdir (str or Path): working directory (local or remote)
            venv_name (str): virtual environment name
            ssh_client (SSHClient, optional): if provided, scripts run remotely
            suppress_output (bool): If True, suppress stdout/stderr from setup commands.
        """
        self.workdir = Path(workdir).resolve() if ssh_client is None else Path(workdir)
        self.venv_name = venv_name
        self.ssh_client = ssh_client
        self.suppress_output = suppress_output
        self.remote_is_windows = None

        if self.ssh_client:
            self.remote_is_windows = self._detect_remote_os()

    def _detect_remote_os(self):
        """Detect if the remote server is Windows. Call this once during init."""
        try:
            # The 'ver' command is specific to Windows and will typically fail on Unix-like systems.
            # We rely on the command execution to fail (raising an exception) to infer a non-Windows OS.
            out, _ = self.ssh_client.execute("ver", suppress_output=True)
            if out and 'windows' in out.lower():
                if not self.suppress_output:
                    print("Detected remote OS: Windows")
                return True
        except Exception:
            # Assuming any error means it's not a Windows shell that knows 'ver'
            pass
        if not self.suppress_output:
            print("Detected remote OS: Unix-like")
        return False
    
    def _get_venv_python(self):
        venv_path = self.workdir / self.venv_name

        if self.ssh_client:
            if self.remote_is_windows:
                return venv_path / "Scripts" / "python.exe"
            else:
                return venv_path / "bin" / "python"
        else:
            if platform.system() == "Windows":
                return venv_path / "Scripts" / "python.exe"
            else:
                return venv_path / "bin" / "python"

    def _get_pip(self):
        venv_path = self.workdir / self.venv_name

        if self.ssh_client:
            if self.remote_is_windows:
                return venv_path / "Scripts" / "pip.exe"
            else:
                return venv_path / "bin" / "pip"
        else:
            if platform.system() == "Windows":
                return venv_path / "Scripts" / "pip.exe"
            else:
                return venv_path / "bin" / "pip"

    def setup_environment(self, requirements):
        """Set up virtual environment and install requirements."""
        stdout = subprocess.DEVNULL if self.suppress_output else None
        stderr = subprocess.DEVNULL if self.suppress_output else None

        if self.ssh_client:
            # Remote
            cmds = [
                f"mkdir -p {self.workdir}",
                f"python3 -m venv {self.workdir / self.venv_name}",
                f"{self._get_pip()} install --upgrade pip",
                f"{self._get_pip()} install -r {requirements}"
            ]
            for cmd in cmds:
                self.ssh_client.execute(cmd, suppress_output=self.suppress_output)
        else:
            # Local
            self.workdir.mkdir(parents=True, exist_ok=True)
            venv_path = self.workdir / self.venv_name
            if not venv_path.exists():
                subprocess.run(
                    [sys.executable, "-m", "venv", str(venv_path)],
                    check=True,
                    stdout=stdout,
                    stderr=stderr
                )
            pip_path = self._get_pip()
            subprocess.run(
                [str(pip_path), "install", "--upgrade", "pip"],
                check=True,
                stdout=stdout,
                stderr=stderr
            )
            subprocess.run(
                [str(pip_path), "install", "-r", str(requirements)],
                check=True,
                stdout=stdout,
                stderr=stderr
            )

    def run_script(self, script_path, args=None, additional_env=None):
        """
        Run a Python script in local or remote environment.
        Output is suppressed unless self.suppress_output is False.
        
        Args:
            script_path (str or Path)
            args (list of str, optional): Arguments to pass to the script.
            additional_env (dict, optional)
        """
        script_path = Path(script_path).resolve()
        
        venv_python = self._get_venv_python()
        
        # Construct the command
        cmd_parts = [str(venv_python), str(script_path)]
        if args:
            cmd_parts.extend(args)
        
        if self.ssh_client:
            # Remote execution: join parts into a command string
            cmd = " ".join(cmd_parts)
            env_str = ""
            if additional_env:
                env_str = " ".join(f"{k}='{v}'" for k, v in additional_env.items())

            full_cmd = f"cd {self.workdir} && {env_str} {cmd}" if env_str else f"cd {self.workdir} && {cmd}"
            # Respect the suppress_output flag
            out, err = self.ssh_client.execute(full_cmd, suppress_output=self.suppress_output)
            return out, err
        else:
            # Local execution: inherit from os.environ and add/override with additional_env
            env = os.environ.copy()
            if additional_env:
                env.update(additional_env)

            # If suppressing, capture output. If not, let it stream to console.
            capture = self.suppress_output
            
            try:
                # When shell=False (safer), pass command as a list.
                result = subprocess.run(
                    cmd_parts,
                    shell=False,
                    check=True,
                    env=env,
                    text=True,
                    capture_output=capture,
                    cwd=self.workdir
                )
                return result
            except subprocess.CalledProcessError as e:
                return e