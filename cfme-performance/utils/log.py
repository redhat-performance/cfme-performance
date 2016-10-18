"""
Framework for the logger and provides additional verbose debug logging.
"""
from utils.conf import cfme_performance
from utils.path import get_rel_path, log_path
import logging
import warnings

# Additional Verbose Debug level
VDEBUG_LEVEL = 9
TRACE_LEVEL = 5

MARKER_LEN = 80


class _RelpathFilter(logging.Filter):
    """Adds the relpath attr to records

    Not actually a filter, this was the least ridiculous way to add custom dynamic
    record attributes and reduce it all down to the ``source`` record attr.

    looks for 'source_file' and 'source_lineno' on the log record, falls back to builtin
    record attributes if they aren't found.

    """
    def filter(self, record):
        try:
            relpath = get_rel_path(record.source_file)
            lineno = record.source_lineno
        except AttributeError:
            relpath = get_rel_path(record.pathname)
            lineno = record.lineno
        if lineno:
            record.source = "{}:{}".format(relpath, lineno)
        else:
            record.source = relpath

        return True


def _showwarning(message, category, filename, lineno, file=None, line=None):
    relpath = get_rel_path(filename)
    if relpath:
        message = "{} from {}:{}: {}".format(category.__name__, relpath, lineno, message)
        logger.warning(message)


def format_marker(mstring, mark="-"):
    """ Creates a marker in log files using a string and leader mark.
    This function uses the constant ``MARKER_LEN`` to determine the length of the marker,
    and then centers the message string between padding made up of ``leader_mark`` characters.
    Args:
        mstring: The message string to be placed in the marker.
        leader_mark: The marker character to use for leading and trailing.
    Returns: The formatted marker string.
    Note: If the message string is too long to fit one character of leader/trailer and
        a space, then the message is returned as is.
    """
    if len(mstring) <= MARKER_LEN - 2:
        # Pad with spaces
        mstring = ' {} '.format(mstring)
        # Format centered, surrounded the leader_mark
        format_spec = '{{:{leader_mark}^{marker_len}}}'.format(
            leader_mark=mark,
            marker_len=MARKER_LEN)
        mstring = format_spec.format(mstring)
    return mstring


def trace(self, message, *args, **kws):
    self._log(TRACE_LEVEL, message, args, **kws)


def vdebug(self, message, *args, **kws):
    self._log(VDEBUG_LEVEL, message, args, **kws)
logging.Logger.vdebug = vdebug

logging.addLevelName(VDEBUG_LEVEL, "VDEBUG")

logging.Logger.trace = trace
logging.addLevelName(TRACE_LEVEL, "TRACE")

logger = logging.getLogger('cfme-performance')
logger.setLevel(cfme_performance['logging']['level'])

formatter = logging.Formatter(
    '%(asctime)s : %(threadName)-11s : %(levelname)7s : %(message)s (%(source)s)')

# Main Log File
filehandler = logging.FileHandler(log_path.join('cfme-performance.log').strpath, 'a')
filehandler.setLevel(cfme_performance['logging']['level'])
filehandler.setFormatter(formatter)
logger.addFilter(_RelpathFilter())
logger.addHandler(filehandler)
logger.propagate = False

# Log warnings to cfme-performance logger
warnings.showwarning = _showwarning
warnings.simplefilter('default')
