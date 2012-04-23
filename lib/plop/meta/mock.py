from plop.meta.base import BaseMeta
import yaml

class MockMeta(BaseMeta):
    """
    Mock persistence layer.
    """

    def __init__(self, config):
        print config
        with open(config, 'r') as config_file:
            contents = config_file.read()
            self.unamedb = yaml.load(contents)['git']
        self.unamedb = self.unamedb['users']
        self.database = {}
        for uname in self.unamedb.keys():
            for pkey in self.unamedb[uname]['keys']:
                self.database[pkey] = uname

    def find_user(self, public_key):
        """
        Find the user by the public_key
        """
        try:
            return self.unamedb[self.database[public_key]]
        except IndexError:
            return None
        except KeyError:
            return None

    def get_user(self, username):
        """
        Get the user out of the in memory dictionary.
        """
        try:
            return self.unamedb[username]
        except IndexError:
            return None
        except KeyError:
            return None
