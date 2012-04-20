import logging
import os
from os.path import basename

import gevent
from gevent_zeromq import zmq
import boto
from boto.s3.key import Key

S3_CONN = boto.connect_s3()
CONTEXT = zmq.Context()

log = logging.getLogger()

def serve(log):
    """
    Start listening for build updates and execute the appropriate
    handlers.
    """
    log.info("Starting up server")
    sock = CONTEXT.socket(zmq.PULL)
    sock.bind("ipc:///git/tmp/build_complete")
    os.chown('/git/tmp/build_complete', -1, 1001)
    os.chmod('/git/tmp/build_complete', 0660)
    try:
        do_serve(log, sock)
    except KeyboardInterrupt:
        log.info("Shutting down . ..")

def upload(log, path, bucket='go-plop'):
    try:
        bucket = S3_CONN.get_bucket(bucket)
    except boto.exception.S3ResponseError:
	log.warn('Creating Bucket')
        bucket = S3_CONN.create_bucket(bucket)
    key = Key(bucket)
    key.key = basename(path)
    log.info('Storing slug: {0}'.format(path))
    key.set_contents_from_filename(path)
    key = Key(bucket)
    key.key = 'current'
    log.debug('Writing current version file')
    key.set_contents_from_string(basename(path))

def do_serve(log, sock):
    message = sock.recv_json()
    while message:
        tar_file = '{0}-{1}.tar.gz'.format(message['project'],
                message['version'])
        template = '/git/tmp/{0}'
        log.debug('Received message')
        gevent.spawn(upload, log, template.format(tar_file))
        message = sock.recv()

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(msg)s")
    serve(log)

if __name__ == '__main__':
    main()
