#pylint: disable=R0921

"""
Base class for the user metadata implementations.
"""

class BaseMeta(object):
    """
    Base metadata object.
    """

    def find_user(self, public_key):
        """
        Return the user based on the public_key.
        """
        raise NotImplementedError()

    def get_user(self, username):
        """
        Return the user based on the username
        """
        raise NotImplementedError()

    def repopath(self, username, reponame):
        """
        return the paths for the user's repos
        """
        user = self.get_user(username)
        try:
            return user['repos'].get(reponame, None)
        except IndexError:
            return None

    def pubkeys(self, username):
        """
        get the public keys for the user.
        """
        user = self.get_user(username)
        try:
            return user['pubkeys']
        except IndexError:
            return None

