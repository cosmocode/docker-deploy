from __future__ import print_function

import os
import sys
import json

from fabric.api import run, env, cd
from fabric.context_managers import shell_env


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULTS = dict(
    TARGET_PORT=6589,
    TARGET_USER='www-data',
)

REQUIRED = (
    'TARGET_HOST',
    'TARGET_PATH',
)


def abort(message, status=1):
    print(message, file=sys.stderr)
    sys.exit(status)


def configure(filename='.fabric-target-conf.json', env='TARGET_CONF', cls=None, **defaults):
    build_job_name = os.getenv('CI_BUILD_NAME')
    branch = os.getenv('CI_BUILD_REF_NAME')

    if not (build_job_name and branch):
        return abort('CI environment variables are missing. You are probably not a real GitLab runner.')

    filepath = os.path.join(PROJECT_DIR, filename)

    if os.path.isfile(filepath):
        with open(filepath, 'r') as fp:
            try:
                data = json.load(fp, cls=cls)
            except ValueError as error:
                return abort('Could not parse JSON from %s: %s' % (filename, error))

    elif env in os.environ:
        data = os.getenv(env)

        try:
            data = json.loads(data, cls=cls)
        except ValueError as error:
            return abort('Could not parse JSON from %s: %s' % (env, error))

    else:
        return abort('Could neither load a configuration from file nor from environment.')

    return parse_configuration(data, build_job_name, branch=branch, **defaults)


def parse_configuration(data, build_job_name, **defaults):
    if build_job_name not in data:
        return abort('Could not find job configuration for %s.' % build_job_name)

    config = dict(defaults, **data.get(build_job_name))

    for option in REQUIRED:
        if not config.get(option):
            return abort('Required configuration parameter %s is missing.' % option)

    return config


CONFIG = configure(**DEFAULTS)

env.hosts = [CONFIG.get('TARGET_HOST')]
env.port = CONFIG.get('TARGET_PORT')
env.user = CONFIG.get('TARGET_USER')

PRE_CMD_ENV = CONFIG.get('PRE_CMD_ENV', {})
POST_CMD_ENV = CONFIG.get('POST_CMD_ENV', {})

BRANCH = CONFIG.get('branch')


def pre():
    if CONFIG.get('PRE_CMDS'):
        [run(cmd) for cmd in CONFIG.get('PRE_CMDS')]


def git_pull():
    run('git fetch --all --quiet')
    run('git checkout --force %s' % BRANCH)
    run('git reset --hard origin/%s' % BRANCH)
    run('git submodule update --init --recursive')


def post():
    if CONFIG.get('POST_CMDS'):
        [run(cmd) for cmd in CONFIG.get('POST_CMDS')]


def deploy():
    with cd(CONFIG.get('TARGET_PATH')):
        with shell_env(**PRE_CMD_ENV):
            pre()
        git_pull()
        with shell_env(**POST_CMD_ENV):
            post()

