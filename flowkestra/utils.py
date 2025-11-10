import paramiko

class SSHClient:
    def __init__(self, hostname, username, password=None, key_filename=None, port=22):
        """
        Initialize SSH client connection details.
        
        Args:
            hostname (str): Remote server IP or domain
            username (str): SSH username
            password (str, optional): SSH password
            key_filename (str, optional): Path to private key file
            port (int, optional): SSH port (default: 22)
        """
        self.hostname = hostname
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.port = port
        self.client = None
        self.sftp = None

    def connect(self):
        """Establish SSH connection."""
        try:
            print(f"Connecting to {self.hostname}...")
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                password=self.password,
                key_filename=self.key_filename,
                timeout=10
            )
            print("Connected successfully!")
        except Exception as e:
            print(f"Failed to connect: {e}")
            raise

    def execute(self, command):
        """Execute a command on the remote server and return its output."""
        if not self.client:
            raise Exception("SSH client not connected. Call connect() first.")
        
        print(f"Executing: {command}")
        stdin, stdout, stderr = self.client.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        if error:
            print(f"Error: {error.strip()}")
        return output.strip(), error.strip()

    def open_sftp(self):
        """Open an SFTP session for file transfer."""
        if not self.client:
            raise Exception("SSH client not connected. Call connect() first.")
        self.sftp = self.client.open_sftp()

    def upload(self, local_path, remote_path):
        """Upload a file to the remote server."""
        if not self.sftp:
            self.open_sftp()
        print(f"Uploading {local_path} → {remote_path}")
        self.sftp.put(local_path, remote_path)

    def download(self, remote_path, local_path):
        """Download a file from the remote server."""
        if not self.sftp:
            self.open_sftp()
        print(f"Downloading {remote_path} → {local_path}")
        self.sftp.get(remote_path, local_path)

    def close(self):
        """Close SSH and SFTP connections."""
        if self.sftp:
            self.sftp.close()
        if self.client:
            self.client.close()
        print("Connection closed.")
