# -*- coding: utf-8 -*-
import time

# The number of resources to create.
N = 6

# The resources of the Openstack infrastructure referenced by their names.
os_resources = ["resource %s" % i for i in xrange(0, N)]


class CentralAgent(object):
    """Mimic the Ceilometer central agent."""

    def poll_resource(self, resource):
        """The function in charge to poll a resource and save the
        result somewhere.
        """
        print("Send poll request to '%s'" % resource)

    def start(self):
        """Main loop for sending periodically the poll requests."""
        while True:
            for resource in os_resources:
                self.poll_resource(resource)
            time.sleep(3)

if __name__ == '__main__':
    central_agent = CentralAgent()
    central_agent.start()
