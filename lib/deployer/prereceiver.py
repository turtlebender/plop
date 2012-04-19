#!/usr/bin/env python

import os
import shutil
import subprocess
import sys
import tempfile
import time 
import contextlib
import zmq

@contextlib.contextmanager
def working_dir(directory):
    curdir= os.getcwd()
    os.chdir(directory)
    try: yield
    finally: os.chdir(curdir)

def build(project_name, newrev):
    base_dir = tempfile.mkdtemp()
    app_dir_name = os.path.join(base_dir, 'app')
    archive_dir_name = os.path.join(app_dir_name, project_name)
    virtualenv_dir = os.path.join(archive_dir_name, '.venv')
    try:
        subprocess.call('virtualenv --distribute {0}'.format(virtualenv_dir), shell=True)
        arch = subprocess.call('git archive {0} | tar -x -C {1}'.format(newrev, archive_dir_name), shell=True)
        with working_dir(archive_dir_name):
            subprocess.check_call('{0}/bin/pip install -i http://pypi.utils.globuscs.info/simple --no-deps -r requirements.txt'.format(virtualenv_dir), shell=True)
        subprocess.check_call('virtualenv --relocatable {0}'.format(virtualenv_dir),shell=True)
        subprocess.check_call('tar -czvf /tmp/{0}.tar.gz -C {1} {2}'.format(project_name, base_dir, 'app'), shell=True)
        context = zmq.Context()
        sock = context.socket(zmq.PUSH)
        sock.connect('ipc:///tmp/build_complete')
        sock.send('gostpy')
        
    finally:
        shutil.rmtree(base_dir)
  
def main():
  for line in sys.stdin.xreadlines():
    old, new, ref = line.strip().split(' ')
    build(os.getcwd().split('/')[-1], new)
  
 
if __name__ == '__main__':
  main()
