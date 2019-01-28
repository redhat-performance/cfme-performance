"""Functions pertaining to determining version of appliance."""
from utils.log import logger
from utils.ssh import SSHClient
import re


def get_current_version_string():
    """Returns string contents of /var/www/miq/vmdb/VERSION"""
    ssh_client = SSHClient()
    exit_status, current_version = ssh_client.run_command('cat /var/www/miq/vmdb/VERSION')
    return current_version.strip()


def get_version():
    """Returns either: '57', '56', '55', '54', 'master', 'unrecognized', depending upon contents of
    /var/www/miq/vmdb/VERSION file on appliance."""
    ver = get_current_version_string()
    if re.search(r'^5\.10', ver):
        return '510'
    if re.search(r'^5\.9', ver):
        return '59'
    if re.search(r'^5\.8', ver):
        return '58'
    elif re.search(r'^5\.7', ver):
        return '57'
    elif re.search(r'^5\.6', ver):
        return '56'
    elif re.search(r'^5\.5', ver):
        return '55'
    elif re.search(r'^5\.4', ver):
        return '54'
    elif re.search(r'^master', ver):
        logger.info('master')
        return 'master'
    return 'unrecognized'
