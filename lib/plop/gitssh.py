#!/usr/bin/env python
import os
import shlex
import sys
import re
from twisted.conch.avatar import ConchUser
from twisted.conch.checkers import SSHPublicKeyDatabase
from twisted.conch.error import ConchError
from twisted.conch.ssh.session import (ISession,
                                       SSHSession,
                                       )
from twisted.conch.ssh.factory import SSHFactory
from twisted.conch.ssh.keys import Key
from twisted.cred.portal import Portal
from twisted.internet import reactor
from twisted.python import components, log

log.startLogging(sys.stderr)


def find_git_shell():
    """
    Find git-shell path.
    Adapted from http://bugs.python.org/file15381/shutil_which.patch
    """
    path = os.environ.get("PATH", os.defpath)
    for directory in path.split(os.pathsep):
        full_path = os.path.join(directory, 'git-shell')
        if (os.path.exists(full_path) and 
                os.access(full_path, (os.F_OK | os.X_OK))):
            return full_path
    raise Exception('Could not find git executable!')


class GitSession(object):

    def __init__(self, user):
        self.user = user

    def execCommand(self, proto, cmd):
        argv = shlex.split(cmd)
        reponame = re.match('(\/[a-zA-Z0-9\-_]+)(.git)?', argv[-1]).group(1)
        sh = self.user.shell

        # Check permissions by mapping requested path to file system path
        repopath = self.user.meta.repopath(self.user.username, reponame)
        if repopath is None:
            raise ConchError('Invalid repository.')
        command = ' '.join(argv[:-1] + ["'%s'" % (repopath,)])
        reactor.spawnProcess(proto, sh,(sh, '-c', command))

    def eofReceived(self): pass

    def closed(self): pass


class GitConchUser(ConchUser):
    shell = find_git_shell()

    def __init__(self, username, meta):
        ConchUser.__init__(self)
        self.username = username
        self.channelLookup.update({"session": SSHSession})
        self.meta = meta

    def logout(self): pass


class GitRealm(object):

    def __init__(self, meta):
        self.meta = meta

    def requestAvatar(self, username, mind, *interfaces):
        user = GitConchUser(username, self.meta)
        return interfaces[0], user, user.logout


class GitPubKeyChecker(SSHPublicKeyDatabase):
    def __init__(self, meta):
        self.meta = meta

    def requestAvatarId(self, credentials):
        pub_key = Key.fromString(credentials.blob).public().toString('OPENSSH')
        return self.meta.find_user(pub_key)['username']

    def checkKey(self, credentials):
        pub_key = Key.fromString(credentials.blob).public().toString('OPENSSH')
        return self.meta.get_user_by_key(pub_key) != None


class GitServer(SSHFactory):

    def __init__(self, privkey):
        pubkey = '.'.join((privkey, 'pub'))
        self.privateKeys = {'ssh-rsa': Key.fromFile(privkey)}
        self.publicKeys = {'ssh-rsa': Key.fromFile(pubkey)}


def main():
    """
    Start up git server
    """
    import yaml
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', dest='config', default='config.yml',
            action='store', help='Configuration yaml file', required=True)
    args = parser.parse_args()
    components.registerAdapter(GitSession, GitConchUser, ISession)
    with open(args.config, 'r') as config:
        config = yaml.load(config.read())
    module_split = config['git']['authentication']['class'].split('.')
    module_string = ".".join(module_split[0:-1])
    module = __import__(module_string)
    for mod in module_split[1:-1]:
        module = getattr(module, mod)
    class_ = getattr(module, module_split[-1])
    authmeta = class_(*config['git']['authentication']['args'])
    portal = Portal(GitRealm(authmeta))
    portal.registerChecker(GitPubKeyChecker(authmeta))
    GitServer.portal = portal
    reactor.listenTCP(config['git']['port'], GitServer(config['git']['key']))
    reactor.run()


if __name__ == '__main__':
    main()
