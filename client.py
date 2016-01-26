import paramiko


class SSHClient(object):
    """ A basic SSH Client
    This class simplifies paramiko's SSHClient so that we can use python's
    built in 'with' statement.
    NOTE: This client will not work without the `with` statement.
    Example:
    with SSHClient(host, username, password) as ssh:
        ssh.exec_command('ls -l')
    """

    def __init__(self, host, username, password, port=22):
        self.__login_info = {'host': host, 'username': username,
                             'password': password, 'port': port}
        self.ssh = None

    def upload(self, local_path, remote_path, callback=None, confirm=True):
        """ Uploads a local file, or file object to a remote path
        Parameters:
            :local_path: Path to file, or file object, to upload
            :remote_path: Remote path to place the file to
            :callback: Optional callback function that accepts bytes
                       transferred so far and the total bytes to be transferred
            :confirm: Whether to do a stat()on the file afterwards to confirm
                      a file size
        Returns:
            An SFTPAttributes object containing attributes about the given file
        """
        with self.ssh.open_sftp() as sftp:
            if isinstance(local_path, file):
                return sftp.putfo(local_path, remote_path, callback=callback,
                                  confirm=confirm)
            else:
                return sftp.put(local_path, remote_path, callback=callback,
                                confirm=confirm)

    def write(self, data, remote_path, mode='w', bufsize=-1):
        """ Writes data to a remote file
        Parameters:
            :data: Data to write
            :remote_path: Remote path to write the string to
            :mode: mode to open the file with
            :bufsize: desired buffering
        """
        with self.ssh.open_sftp() as sftp:
            with sftp.file(remote_path, mode=mode, bufsize=bufsize) as fp:
                fp.write(data)

    def download(self, remote_path, local_path, callback=None, confirm=True):
        """ Downloads a file from a remote server to a local path
        Parameters:
            :remote_path: Remote path to file to download
            :local_path: Where to place the file locally
            :callback: Optional callback function that accepts bytes
                       transferred so far and the total bytes to be transferred
            :confirm: Whether to do a stat()on the file afterwards to confirm
                      a file size
        Returns:
            An SFTPAttributes object containing attributes about the given file
        """
        with self.ssh.open_sftp() as sftp:
            return sftp.get(remote_path, local_path)

    def read(self, remote_path, mode='r', bufsize=-1):
        """ Reads data from a remote file
        Parameters:
            :remote_path: Remote path to write the string to
            :mode: mode to open the file with
            :bufsize: desired buffering
        Returns:
            A buffer of the data ready to be processed
        """
        with self.ssh.open_sftp() as sftp:
            with sftp.file(remote_path, mode=mode, bufsize=bufsize) as fp:
                data = fp.read()
        return data

    def exec_command(self, command):
        """ Provides a nice wrapper to execute commands over ssh
        Parameters:
            :command: Command to execute (string representation)
        Returns:
            The output from both stdout and stderr for the command
        """
        _, stdin, stderr = self.ssh.exec_command(command)
        return stdin.read(), stderr.read()

    def exec_commands(self, commands):
        """ Provides a nice wrapper to execute multiple commands over ssh
        Parameters:
            :command: Command to execute (list of strings representation)
        Returns:
            The output from both stdout and stderr for the commands
        """
        stdin, stdout, stderr = self.ssh.exec_command(commands[0])
        stdin.write('\n'.join(commands[1:]) + '\n')
        stdin.write('exit\n')
        stdin.flush()
        return stdout.read(), stderr.read()

    def close(self):
        self.ssh.close()

    def __enter__(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.load_system_host_keys()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.__login_info['host'],
                         username=self.__login_info['username'],
                         password=self.__login_info['password'],
                         port=self.__login_info['port'])
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
