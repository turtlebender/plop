from gevent import spawn
from gevent_zeromq import zmq
import os
import boto
from boto.s3.key import Key
from os.path import basename

S3_CONN = boto.connect_s3()
CONTEXT = zmq.Context()

def serve():
    """
    Start listening for build updates and execute the appropriate
    handlers.
    """
    sock = CONTEXT.socket(zmq.PULL)
    sock.bind("ipc:///git/tmp/build_complete")
    os.chown('/git/tmp/build_complete', -1, 1001)
    os.chmod('/git/tmp/build_complete', 0660)
    do_serve(sock)

def upload(path, bucket='plop'):
    bucket = S3_CONN.get_bucket(bucket)
    key = Key(bucket)
    key.key = basename(path)
    key.set_contents_from_filename(path)
    key = Key(bucket)
    key.key = 'current'
    key.set_contents(basename(path))

def do_serve(sock):
    message = sock.recv_json()
    while message:
        tar_file = '{0}-{1}.tar.gz'.format(message['project'],
                message['version'])
        template = '/git/tmp/{0}'
        spawn(upload, template.format(tar_file))
        message = sock.recv()

if __name__ == '__main__':
    serve()
