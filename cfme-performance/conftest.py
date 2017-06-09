"""pytest plugins"""
import atexit
from utils import log
from utils import collectd
import collections
import diaper
import pytest
from functools import partial
from utils import ssh
from utils.conf import cfme_performance as perf_data
from utils.sprout import SproutClient
from wait_for import wait_for as wait_for_mod
import fixtures
from pkgutil import iter_modules


#: A dict of tests, and their state at various test phases
test_tracking = collections.defaultdict(dict)


@pytest.fixture(scope='session')
def logger():
    return log.logger


def at_exit(f, *args, **kwargs):
    """Diaper-protected atexit handler registering. Same syntax as atexit.register()"""
    return atexit.register(lambda: diaper(f, *args, **kwargs))


def pytest_addoption(parser):
    group = parser.getgroup('perf')
    group.addoption('--appliance', dest='appliance', default=None,
                    help="Run tests with the appliance ip as command line option.")
    group.addoption('--appliance-name', dest='appliance_name', default=None,
                    help="Run tests with the appliance name as command line option.")
    group.addoption('--replication-master-ip', dest='replication_master_ip', default=None,
                    help="Run tests with the replication master ip as command line option.")
    group.addoption('--replication-master-name', dest='replication_master_name', default=None,
                    help="Run tests with the replication master name as command line option.")
    group._addoption('--use-sprout', dest='use_sprout', action='store_true',
                     default=False, help="Use Sprout for provisioning appliances.")
    group._addoption('--sprout-desc', dest='sprout_desc', default='Perf-wrokload-tests',
                     help="Set description of the pool.")
    group._addoption('--sprout-appliances', dest='sprout_appliances', type=int,
                     default=1, help="How many Sprout appliances to use?.")
    group._addoption('--sprout-group', dest='sprout_group', default='downstream-56z',
                     help="Which stream to use.")
    group._addoption('--sprout-timeout', dest='sprout_timeout', type=int,
                     default=10080, help="How many minutes is the lease timeout.")
    group._addoption('--sprout-version', dest='sprout_version',
                     default=None, help="Which version to use.")
    group._addoption('--sprout-override-ram', dest='sprout_override_ram', type=int,
                     default=0, help="Override RAM (MB). 0 means no override.")
    group._addoption('--sprout-override-cpu', dest='sprout_override_cpu', type=int,
                     default=0, help="Override CPU core count. 0 means no override.")
    group._addoption('--use-collectd', dest='use_collectd', action='store_true', default=False,
                    help="Run collectd on appliance and upload data on monitor-host.")


def pytest_configure(config):
    if config.option.use_sprout:
        # Using sprout
        try:
            sprout_client = SproutClient.from_config()
            logger().info(
                "Requesting {} appliances from Sprout at {}\n".format(
                    config.option.sprout_appliances, sprout_client.api_entry))
            pool_id = sprout_client.request_appliances(
                config.option.sprout_group,
                count=config.option.sprout_appliances,
                lease_time=config.option.sprout_timeout,
                version=config.option.sprout_version,
                cpu=config.option.sprout_override_cpu or None,
                ram=config.option.sprout_override_ram or None,
            )
            wait_for = partial(wait_for_mod)
            logger().info("Pool {}. Waiting for fulfillment ...\n".format(pool_id))
            sprout_pool = pool_id
            at_exit(sprout_client.destroy_pool, sprout_pool)
            if config.option.sprout_desc is not None:
                sprout_client.set_pool_description(
                    pool_id, str(config.option.sprout_desc))
            try:
                result = wait_for(
                    lambda: sprout_client.request_check(sprout_pool)["fulfilled"],
                    num_sec=3600,
                    delay=5,
                    message="requesting appliances was fulfilled"
                )
            except:
                logger().info("Destroying the pool on error.\n")
                sprout_client.destroy_pool(pool_id)
                raise
            logger().info("Provisioning took {0:.1f} seconds\n".format(result.duration))
            request = sprout_client.request_check(sprout_pool)
            # Push an appliance to the stack to have proper reference for test collection
            perf_data['appliance']['ip_address'] = request["appliances"][0]["ip_address"]
            perf_data['appliance']['appliance_name'] = 'CFME-R0000-SPROUT-LATEST'
            logger().info("Sprout Appliances provisioning completed\n")
        except Exception as e:
            logger().error(e)
            logger().error("Exception occured while provisioning from sprout")
    if config.option.appliance:
        perf_data['appliance']['ip_address'] = config.option.appliance
    if config.option.appliance_name:
        perf_data['appliance']['appliance_name'] = config.option.appliance_name
    logger().info('Appliance IP is {}'.format(perf_data['appliance']['ip_address']))
    logger().info('Appliance name is {}'.format(perf_data['appliance']['appliance_name']))
    if config.option.replication_master_ip:
        perf_data['replication_master']['ip_address'] = config.option.replication_master_ip
        logger().info('Replication Master IP is {}'.format(
            perf_data['replication_master']['ip_address']))
    if config.option.replication_master_name:
        perf_data['replication_master']['appliance_name'] = config.option.replication_master_name
        logger().info('Replication Master appliance name is {}'.format(
            perf_data['replication_master']['appliance_name']))
    if config.option.use_collectd and config.option.use_sprout:
        collectd.setup_collectd(perf_data)


def pytest_collection_modifyitems(session, config, items):
    logger().info(log.format_marker('Starting new test run', mark="="))
    expression = config.getvalue('keyword') or False
    expr_string = ', will filter with "{}"'.format(expression) if expression else ''
    logger().info('Collected {} items{}'.format(len(items), expr_string))


def pytest_exception_interact(node, call, report):
    # Despite the name, call.excinfo is a py.code.ExceptionInfo object. Its traceback property
    # is similarly a py.code.TracebackEntry. The following lines, including "entry.lineno+1" are
    # based on the code there, which does unintuitive things with a traceback's line number.
    # This is the same code that powers py.test's output, so we gain py.test's magical ability
    # to get useful AssertionError output by doing it this way, which makes the voodoo worth it.
    entry = call.excinfo.traceback.getcrashentry()
    logger().error(call.excinfo.getrepr(),
        extra={'source_file': entry.path, 'source_lineno': entry.lineno + 1})


@pytest.mark.hookwrapper
def pytest_runtest_logreport(report):
    yield
    test_tracking[_format_nodeid(report.nodeid, False)][report.when] = report.outcome
    if report.when == 'teardown':
        path, lineno, domaininfo = report.location
        test_status = _test_status(_format_nodeid(report.nodeid, False))
        logger().info(log.format_marker('{} result: {}'.format(_format_nodeid(report.nodeid),
                test_status)),
            extra={'source_file': path, 'source_lineno': lineno})
    if report.outcome == "skipped":
        # Usualy longrepr's a tuple, other times it isn't... :(
        try:
            longrepr = report.longrepr[-1]
        except AttributeError:
            longrepr = str(report.longrepr)

        logger().info(log.format_marker(longrepr))


@pytest.mark.hookwrapper
def pytest_runtest_setup(item):
    path, lineno, domaininfo = item.location
    logger().info(log.format_marker(_format_nodeid(item.nodeid), mark="-"),
        extra={'source_file': path, 'source_lineno': lineno})
    yield


def pytest_sessionfinish(session, exitstatus):
    c = collections.Counter()
    for test in test_tracking:
        c[_test_status(test)] += 1
    # Prepend a total to the summary list
    results = ['total: {}'.format(sum(c.values()))] + map(
        lambda n: '{}: {}'.format(n[0], n[1]), c.items())
    # Then join it with commas
    summary = ', '.join(results)
    logger().info(log.format_marker('Finished test run', mark='='))
    logger().info(log.format_marker(str(summary), mark='='))
    for session in ssh._client_session:
        try:
            session.close()
        except:
            pass


def _test_status(test_name):
    test_phase = test_tracking[test_name]
    # Test failure in setup or teardown is an error, which pytest doesn't report internally
    if 'failed' in (test_phase.get('setup', 'failed'), test_phase.get('teardown', 'failed')):
        return 'error'
    # A test can also be skipped
    elif 'skipped' in test_phase.get('setup', 'skipped'):
        return 'skipped'
    # Otherwise, report the call phase outcome (passed, skipped, or failed)
    else:
        return test_phase['call']


def _format_nodeid(nodeid, strip_filename=True):
    # Remove test class instances and filenames, replace with a dot to impersonate a method call
    nodeid = nodeid.replace('::()::', '.')
    # Trim double-colons to single
    nodeid = nodeid.replace('::', ':')
    # Strip filename (everything before and including the first colon)
    if strip_filename:
        try:
            return nodeid.split(':', 1)[1]
        except IndexError:
            # No colon to split on, return the whole nodeid
            return nodeid
    else:
        return nodeid


def _pytest_plugins_generator(*extension_pkgs):
    # Finds all submodules in pytest extension packages and loads them
    for extension_pkg in extension_pkgs:
        path = extension_pkg.__path__
        prefix = '%s.' % extension_pkg.__name__
        for importer, modname, is_package in iter_modules(path, prefix):
            yield modname

pytest_plugins = tuple(_pytest_plugins_generator(fixtures))
