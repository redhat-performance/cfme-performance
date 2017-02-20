"""SSH client and SSH Tailing client."""
from collections import namedtuple
from utils.conf import cfme_performance
from utils.log import logger
import paramiko
import socket
import sys

RUNCMD_TIMEOUT = 1200.0
SSHResult = namedtuple("SSHResult", ["rc", "output"])

_client_session = []


class SSHClient(paramiko.SSHClient):
    """paramiko.SSHClient wrapper
    Allows copying/overriding and use as a context manager
    Constructor kwargs are handed directly to paramiko.SSHClient.connect()
    """
    def __init__(self, stream_output=False, **connect_kwargs):
        logger.vdebug('ssh.__init__')
        super(SSHClient, self).__init__()
        self._streaming = stream_output

        default_connect_kwargs = {
            'username': cfme_performance['appliance']['ssh']['username'],
            'password': cfme_performance['appliance']['ssh']['password'],
            'hostname': cfme_performance['appliance']['ip_address'],
            'port': 22,
            'timeout': 10,
            'allow_agent': False,
            'look_for_keys': False,
            'gss_auth': False
        }

        # Overlay defaults with any passed-in kwargs and store
        default_connect_kwargs.update(connect_kwargs)
        self._connect_kwargs = default_connect_kwargs
        self.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        _client_session.append(self)

    def __repr__(self):
        return "<SSHClient hostname={} port={}>".format(
            repr(self._connect_kwargs.get("hostname")),
            repr(self._connect_kwargs.get("port", 22)))

    def __call__(self, **connect_kwargs):
        logger.vdebug('ssh.__call__')
        # Update a copy of this instance's connect kwargs with passed in kwargs,
        # then return a new instance with the updated kwargs
        new_connect_kwargs = dict(self._connect_kwargs)
        new_connect_kwargs.update(connect_kwargs)
        # pass the key state if the hostname is the same, under the assumption that the same
        # host will still have keys installed if they have already been
        new_client = SSHClient(**new_connect_kwargs)
        return new_client

    def __enter__(self):
        logger.vdebug('ssh.__enter__')
        self.connect()
        return self

    def __exit__(self, *args, **kwargs):
        # Noop, call close explicitly to shut down the transport
        # It will be reopened automatically on next command
        pass

    def __del__(self):
        self.close()

    def close(self):
        try:
            _client_session.remove(self)
        except:
            pass
        super(SSHClient, self).close()

    @property
    def connected(self):
        return self._transport and self._transport.active

    def connect(self, hostname=None, **kwargs):
        """See paramiko.SSHClient.connect"""
        logger.vdebug('ssh.connect')
        if hostname and hostname != self._connect_kwargs['hostname']:
            self._connect_kwargs['hostname'] = hostname
            self.close()

        if not self.connected:
            self._connect_kwargs.update(kwargs)
            return super(SSHClient, self).connect(**self._connect_kwargs)

    def open_sftp(self, *args, **kwargs):
        logger.vdebug('ssh.open_sftp')
        self.connect()
        return super(SSHClient, self).open_sftp(*args, **kwargs)

    def get_transport(self, *args, **kwargs):
        if self.connected:
            logger.vdebug('reusing ssh transport')
        else:
            logger.vdebug('connecting new ssh transport')
            self.connect()
        return super(SSHClient, self).get_transport(*args, **kwargs)

    def run_command(self, command, timeout=RUNCMD_TIMEOUT, reraise=False, log_less=False, ignore_stderr=False):
        if log_less:
            logger.info("Running command `{}...(truncated)...`".format(command[:30]))
        else:
            logger.info("Running command `{}`".format(command))
        template = '{}\n'
        command = template.format(command)

        output = ''
        try:
            session = self.get_transport().open_session()
            if timeout:
                session.settimeout(float(timeout))
            session.exec_command(command)
            stdout = session.makefile()
            stderr = session.makefile_stderr()
            while True:
                if session.recv_ready:
                    for line in stdout:
                        output += line
                        if self._streaming:
                            sys.stdout.write(line)

                if session.recv_stderr_ready and not ignore_stderr:
                    for line in stderr:
                        output += line
                        if self._streaming:
                            sys.stderr.write(line)

                if session.exit_status_ready():
                    break
            exit_status = session.recv_exit_status()
            return SSHResult(exit_status, output)
        except paramiko.SSHException as exc:
            if reraise:
                raise
            else:
                logger.exception(exc)
        except socket.timeout as e:
            logger.error("Command `%s` timed out.", command)
            logger.exception(e)
            logger.error("Output of the command before it failed was:\n%s", output)
            raise

        return SSHResult(1, None)

#   added ignore_stderr option to handle ScannerError issue, which arises because
#   the output contains stderr, and thus yaml.load fails
    def run_rails_command(self, command, timeout=RUNCMD_TIMEOUT, ignore_stderr=False):
        logger.info("Running rails command `%s`", command)
        return self.run_command('cd /var/www/miq/vmdb; bin/rails runner {}'.format(command),
            timeout=timeout, ignore_stderr=ignore_stderr)

    def run_rails_console(self, command, sandbox=False, timeout=RUNCMD_TIMEOUT, log_less=False):
        """Runs Ruby inside of rails console. stderr is thrown away right now but could prove useful
        for future performance analysis of the queries rails runs.  The command is encapsulated by
        double quotes. Sandbox rolls back all changes made to the database if used.
        """
        if sandbox:
            return self.run_command('cd /var/www/miq/vmdb; echo \"' + command + '\" '
                '| bundle exec bin/rails c -s 2> /dev/null', timeout=timeout, log_less=log_less)
        return self.run_command('cd /var/www/miq/vmdb; echo \"' + command + '\" '
            '| bundle exec bin/rails c 2> /dev/null', timeout=timeout, log_less=log_less)

    def run_rake_command(self, command, timeout=RUNCMD_TIMEOUT):
        logger.info("Running rake command `%s`", command)
        return self.run_command('cd /var/www/miq/vmdb; bin/rake {}'.format(command),
            timeout=timeout)


class SSHTail(SSHClient):

    def __init__(self, remote_filename, **connect_kwargs):
        super(SSHTail, self).__init__(stream_output=False, **connect_kwargs)
        self._remote_filename = remote_filename
        self._sftp_client = None
        self._remote_file_size = None

    def __iter__(self):
        with self as sshtail:
            fstat = sshtail._sftp_client.stat(self._remote_filename)
            if self._remote_file_size is not None:
                if self._remote_file_size < fstat.st_size:
                    remote_file = self._sftp_client.open(self._remote_filename, 'r')
                    remote_file.seek(self._remote_file_size, 0)
                    while (remote_file.tell() < fstat.st_size):
                        line = remote_file.readline().rstrip()
                        yield line
            self._remote_file_size = fstat.st_size

    def __enter__(self):
        self.connect(**self._connect_kwargs)
        self._sftp_client = self.open_sftp()
        return self

    def __exit__(self, *args, **kwargs):
        self._sftp_client.close()

    def set_initial_file_end(self):
        with self as sshtail:
            fstat = sshtail._sftp_client.stat(self._remote_filename)
            self._remote_file_size = fstat.st_size  # Seed initial size of file
