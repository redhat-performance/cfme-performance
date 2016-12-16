"""Autoload yaml config files."""
from py.path import local
from yaycl import Config
import os
import sys

base_dir = local(os.path.abspath(__file__)).new(basename='..')
yaycl_options = {
    'config_dir': base_dir.join('conf').strpath,
    'extension': '.yml'
}

crypt_key_file = base_dir.join('.yaml_key')
if crypt_key_file.exists():
    yaycl_options['crypt_key_file'] = crypt_key_file.strpath

sys.modules[__name__] = Config(**yaycl_options)
