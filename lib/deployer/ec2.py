import functools
import json
import os
import sys

import boto
from clint import args
from clint.textui import colored, indent, puts

class ElbHelper(object):

    def __init__(self, **credentials):
        self.ec2_conn = boto.connect_ec2(**credentials)
        self.elb_conn = boto.connect_elb(**credentials)

    def instance_in(self, instance_id, load_balancer):
        instance_ids = map(lambda x: x.id, load_balancer.instances)
        return load_balancer if instance_id in instance_ids else None

    def instances(self):
        for reserv in self.ec2_conn.get_all_instances():
            instance = reserv.instances[0]
            print "{0} ({1})".format(instance.tags['Name'], instance.id)

    def get_instance(self, name):
        filters = {'tag:Name': name}
        return self.ec2_conn.get_all_instances(filters=filters)[0].instances[0]

    def get_load_balancers(self, name):
        try:
            instance_id = self.get_instance(name).id
        except:
            print colored.red("Unknown instances: {0}".format(name))
            sys.exit(1)
        test = functools.partial(self.instance_in, instance_id)
        return filter(lambda x: x is not None, map(test,
            self.elb_conn.get_all_load_balancers()))

    def remove(self, name):
        lbs = self.get_load_balancers(name)
        instance = self.get_instance(name)
        with open('.{0}'.format(name), 'w') as config:
            config.write(json.dumps(map(lambda lb: lb.name, lbs)))
        for load_balancer in lbs:
            self.elb_conn.deregister_instances(load_balancer.name, 
                    [instance.id])

    def readd(self, name):
        if not os.path.exists('.{0}'.format(name)):
            with indent(3):
                puts(colored.red("I can't find a cached list of elbs."))
                puts(colored.red("Did you use remove first?"))
                sys.exit(1)

        with open('.{0}'.format(name), 'r') as config:
            lbs = json.loads(config.read())

        for load_balancer in lbs:
            self.elb_conn.register_instances(load_balancer, 
                    [self.get_instance(name).id])

    def list(self, name):
        with indent(0, quote=colored.red('----> ')):
            for load_balancer in self.get_load_balancers(name):
                puts(load_balancer.name)
                with indent(4):
                    puts(load_balancer.dns_name)
        

def main(operation, args):
    helper = ElbHelper()
    if hasattr(helper, operation):
        getattr(helper, operation)(*args)

def usage():
    print(colored.red("This will be usage"))

if __name__ == '__main__':
    main(args.all[0], args.all[1:])
