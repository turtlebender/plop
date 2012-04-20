#!/usr/bin/env python

import os
import shutil
import subprocess
import tempfile
from clint import piped_in
import contextlib
import zmq
from plop import gitversion, EVENT_TYPE_KEY. BUILD_COMPLETE_VALUE

CREATE_VIRTUALENV_CMD = 'virtualenv --distribute {0}'
GIT_ARCHIVE_CMD = 'git archive {0} | tar -x -C {1}'
PIP_INSTALL_CMD = '{0}/bin/pip install -i {1} --no-deps -r requirements.txt'
RELOCATABLE_VENV_CMD = 'virtualenv --relocatable {0}'
TAR_CMD = 'tar -czvf /tmp/{0}-{1}.tar.gz -C {2} {3}'
DEF_MIRROR = 'http://pypi.utils.globuscs.info/simple'
DEF_SOCKET = 'ipc:///tmp/build_complete'

@contextlib.contextmanager
def working_dir(directory):
    curdir = os.getcwd()
    os.chdir(directory)
    try: 
        yield
    finally: 
        os.chdir(curdir)


def build(project_name, newrev, ref_name, socket_addr, pip_mirror):
    base_dir = tempfile.mkdtemp()
    app_dir_name = os.path.join(base_dir, 'app')
    os.mkdir(app_dir_name)
    archive_dir_name = os.path.join(app_dir_name, project_name)
    os.mkdir(archive_dir_name)
    virtualenv_parent = tempfile.mkdtemp()
    virtualenv_dir = os.path.join(virtualenv_parent, project_name)
    os.mkdir(virtualenv_dir)
    try:
        subprocess.check_call(CREATE_VIRTUALENV_CMD.format(virtualenv_dir),
            shell=True)
        subprocess.check_call(GIT_ARCHIVE_CMD.format(newrev,
            archive_dir_name), shell=True)
        with working_dir(archive_dir_name):
            install = PIP_INSTALL_CMD.format(os.path.abspath(virtualenv_dir),
                    pip_mirror)
            subprocess.check_call(install, shell=True)
        relocatable_venv = RELOCATABLE_VENV_CMD.format(virtualenv_dir)
        subprocess.check_call(relocatable_venv, shell=True)
        version = gitversion.get_version(ref_name=ref_name, rev=newrev)
        tar = TAR_CMD.format(project_name, version, 
                virtualenv_parent, project_name)
        subprocess.check_call(tar, shell=True)
        context = zmq.Context()
        sock = context.socket(zmq.PUSH)
        sock.connect(socket_addr)
        sock.send_json({EVENT_TYPE_KEY=BUILD_COMPLETE_VALUE,
            'project':'project_name', 'version':'version'})

    finally:
        shutil.rmtree(base_dir)
        shutil.rmtree(virtualenv_dir)

def main():
    line = piped_in()
    old, new, ref = line.strip().split(' ')
    project_name = os.getcwd().split('/')[-1]
    env = os.environ
    pip_mirror = env['PIP_MIRROR'] if 'PIP_MIRROR' in env else DEF_MIRROR
    socket = env['BUILD_SOCKET'] if 'BUILD_SOCKET' in env else DEF_SOCKET
    build(project_name, new, ref.split('/')[-1], socket, pip_mirror)

if __name__ == '__main__':
    main()
