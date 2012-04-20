import zmq
import os
import shutil

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
    message = sock.recv_json()
    while message:
        template = '/git/tmp/{0}-{1}.tar.gz'
        source_file = template.format(message['project'], message['version'])
        shutil.copyfile(source_file,
                os.path.expanduser('~/{0}.tar.gz'.format(message)))
        message = sock.recv()

if __name__ == '__main__':
    serve()
