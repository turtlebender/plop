import logging
import os
from os.path import basename
import re

import boto
from boto.s3.key import Key
import gevent
from gevent_zeromq import zmq
from plop import EVENT_TYPE_KEY, BUILD_COMPLETE_VALUE
from plop.ec2 import ElbHelper
from zmq.core.error import ZMQError

CONTEXT = zmq.Context()

LOG = logging.getLogger()


NO_BUCKET = 'You must supply the s3_bucket value in your configuration'
NO_SERVER_SOCKET = 'You must specify the socket upon which the server listens'
NO_SOCKET_GROUP = 'To use the ipc protocol you must specify a socket group'

class PlopServer(object):

    """
    Server to handle updates from the git listeners as well as provision
    requests.
    """
    def __init__(self, config):
        try:
            self.bucket = config['s3_bucket']
        except IndexError:
            raise AssertionError(NO_BUCKET)
        try:
            self.server_socket = config['server_socket']
        except IndexError:
            raise AssertionError(NO_SERVER_SOCKET)
        if 'ipc' in self.server_socket:
            try:
                self.socket_group = config['socket_group']
            except IndexError:
                raise AssertionError(NO_SOCKET_GROUP)
        try:
            self.sock = CONTEXT.socket(zmq.PULL)
            self.sock.bind(self.server_socket)
        except ZMQError as zmqerror:
            message = zmqerror.message
            message = 'Unable to initialize zeromq: {0}'.format(message)
            raise AssertionError(message)
        if 'aws_access_key_id' in config and 'aws_secret_access_key' in config:
            self.s3_conn = boto.connect_s3(config['aws_access_key_id'],
                    config['aws_secret_access_key'])
            self.elbheper = ElbHelper(config['aws_access_key_id'],
                config['aws_secret_access_key'])
        else:
            self.s3_conn = boto.connect_s3()
            self.elbhelper = ElbHelper()

    def serve(self):
        """
        Start listening for build updates and execute the appropriate
        handlers.
        """
        LOG.info("Starting up server")

        if 'ipc://' in self.server_socket:
            path = re.match('ipc\:\/\/(.*)', self.server_socket).group(1)
            os.chown(path, -1, self.socket_group)
            os.chmod(path, 0660)

        try:
            self.do_serve(self.sock)
        except KeyboardInterrupt:
            LOG.info("Shutting down . ..")

    def upload(self, path):
        """
        When a message is received, upload the file to S3.
        """
        try:
            bucket = self.s3_conn.get_bucket(self.bucket)
        except boto.exception.S3ResponseError:
            LOG.warn('Creating Bucket')
            bucket = self.s3_conn.create_bucket(self.bucket)
        key = Key(bucket)
        key.key = basename(path)
        LOG.info('Storing slug: {0}'.format(path))
        key.set_contents_from_filename(path)
        key = Key(bucket)
        if 'dev' in path:
            key.key = 'current'
            LOG.debug('Writing current version file')
            key.set_contents_from_string(basename(path))

    def do_serve(self, sock):
        """
        The actual server logic
        """
        message = sock.recv_json()
        while message:
            tar_file = '{0}-{1}.tar.gz'.format(message['project'],
                    message['version'])
            template = '/git/tmp/{0}'
            LOG.debug('Received message')
            if message[EVENT_TYPE_KEY] == BUILD_COMPLETE_VALUE:
                gevent.spawn(self.upload, template.format(tar_file))
            message = sock.recv()

def main():
    """
    Execute as a standalone program
    """
    from clint.textui import colored
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(msg)s")
    try:
        server = PlopServer({
            's3_bucket':'go_plop',
            'server_socket':'ipc:///git/tmp/build_complete',
            'socket_group':1001
            })
    except AssertionError as error:
        print colored.red(error.message)
    server.serve()

if __name__ == '__main__':
    main()
