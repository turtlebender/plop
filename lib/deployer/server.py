import zmq
import time
import os
import shutil

context = zmq.Context()
sock = context.socket(zmq.PULL)
sock.bind("ipc:///git/tmp/build_complete")
os.chown('/git/tmp/build_complete', -1, 1001)
os.chmod('/git/tmp/build_complete', 0660)
      
message = sock.recv()
while message:
    shutil.copyfile('/git/tmp/{0}.tar.gz'.format(message), os.path.expanduser('~/{0}.tar.gz'.format(message)))
    message = sock.recv()
