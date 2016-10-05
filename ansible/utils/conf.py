import os
from py.path import local
import sys
from yaycl import Config

BASE_DIR = local(os.path.abspath(__file__)).new(basename='..')

yaycl_options = {
    'config_dir': BASE_DIR.join('group_vars').strpath,
    'extension': '.yml'
}

sys.modules[__name__] = Config(**yaycl_options)
