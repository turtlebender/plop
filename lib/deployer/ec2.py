import functools
import boto
import sys
from clint.textui import colored, indent, puts

class ElbHelper(object):

    def __init__(self, **credentials):
        self.ec2_conn = boto.connect_ec2(**credentials)
        self.elb_conn = boto.connect_elb(**credentials)

    def instance_in(self, instance_id, load_balancer):
        return load_balancer if instance_id in map(lambda x: x.id, load_balancer.instances) else None

    def get_instance(self, name):
        return self.ec2_conn.get_all_instances(filters={'tag:Name':name})[0].instances[0]

    def get_load_balancers(self, name):
        try:
            instance_id = self.get_instance(name).id
        except:
            print colored.red("Unknown instances: {0}".format(name))
            sys.exit(1)
        test = functools.partial(self.instance_in, instance_id)
        return filter(lambda x: x is not None, map(test,
            self.elb_conn.get_all_load_balancers()))

if __name__ == '__main__':
    helper = ElbHelper()
    with indent(0, quote=colored.red('----> ')):
        for lb in helper.get_load_balancers(sys.argv[1]):
            puts(lb.name)
            with indent(4):
                puts(lb.dns_name)

