import os
import sys
import subprocess
from pathlib import Path
import platform

from flowkestra.utils import SSHClient

class Runner:
    def __init__(self, workdir, venv_name="venv", ssh_client: SSHClient =None):
        """
        Args:
            workdir (str or Path): working directory (local or remote)
            venv_name (str): virtual environment name
            ssh_client (SSHClient, optional): if provided, scripts run remotely
        """
        self.workdir = Path(workdir).resolve() if ssh_client is None else Path(workdir)
        self.venv_name = venv_name
        self.ssh_client = ssh_client
        self.remote_is_windows = None

        if self.ssh_client:
            self.remote_is_windows = self._detect_remote_os()

    def _detect_remote_os(self):
        """Detect if the remote server is Windows. Call this once during init."""
        try:
            out, _ = self.ssh_client.execute("ver")  # Windows returns version info
            if out:
                print("Detected remote OS: Windows")
                return True
        except:
            pass
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
        if self.ssh_client:
            # Remote
            cmds = [
                f"mkdir -p {self.workdir}",
                f"python3 -m venv {self.workdir / self.venv_name}",
                f"{self._get_pip()} install --upgrade pip",
                f"{self._get_pip()} install -r {requirements}"
            ]
            for cmd in cmds:
                out, err = self.ssh_client.execute(cmd)
                if out:
                    print(out)
                if err:
                    print(err)
            print(f"[REMOTE] Environment ready at {self.workdir}")
        else:
            # Local
            self.workdir.mkdir(parents=True, exist_ok=True)
            venv_path = self.workdir / self.venv_name
            if not venv_path.exists():
                subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
            pip_path = self._get_pip()
            subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
            subprocess.run([str(pip_path), "install", "-r", str(requirements)], check=True)
            print(f"[LOCAL] Environment ready at {self.workdir}")

    def run_script(self, script_path, additional_env=None):
        """
        Run a Python script in local or remote environment.
        
        Args:
            script_path (str or Path)
            additional_env (dict, optional)
        """
        script_path = Path(script_path).resolve()
        env = os.environ.copy()
        if additional_env:
            env.update(additional_env)

        venv_python = self._get_venv_python()
        cmd = f"{venv_python} {script_path}"

        if self.ssh_client:
            # Prepare environment string for remote shell
            env_str = " ".join(f"{k}='{v}'" for k, v in env.items())
            # Prepend 'cd' command to ensure execution in workdir
            full_cmd = f"cd {self.workdir} && {env_str} {cmd}" if env_str else f"cd {self.workdir} && {cmd}"
            out, err = self.ssh_client.execute(full_cmd)
            if out:
                print(out)
            if err:
                print(err)
            return out, err
        else:
            print(f"[LOCAL] Running: {cmd}")
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    check=True,
                    env=env,
                    text=True,
                    capture_output=True,
                    cwd=self.workdir
                )
                print(result.stdout)
                if result.stderr:
                    print(result.stderr)
                return result
            except subprocess.CalledProcessError as e:
                print(e.stderr)
                return e
