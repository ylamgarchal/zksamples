# -*- coding: utf-8 -*-
import bisect
import functools
import time
from kazoo import client as kz_client
import uuid
import hashlib

# The number of resources to create.
N = 6

# The resources of the Openstack infrastructure referenced by their names.
os_resources = ["resource %s" % i for i in xrange(0, N)]
os_resources_hash = {}

for resource in os_resources:
    md5_sum = hashlib.md5()
    md5_sum.update(resource)
    os_resources_hash[resource] = md5_sum.hexdigest()

class CentralAgent(object):
    """Mimic the improved Ceilometer central agent."""

    def __init__(self):
        self._my_client = kz_client.KazooClient(hosts='127.0.0.1:2181',
                                                timeout=5)
        self._my_client.add_listener(CentralAgent.my_listener)
        self._my_resources = []
        self._my_id = str(uuid.uuid4())
        print("Agent id: %s" % self._my_id)

    @staticmethod
    def my_listener(state):
        """Print a message when the client is connected to the ZK server."""
        if state == kz_client.KazooState.CONNECTED:
            print("Client connected !")

    def poll_resource(self, resource):
        """The function in charge to poll a resource and save the
        result somewhere.
        """
        print("Send poll request to '%s'" % resource)

    @staticmethod
    def _get_ring(members):
        ring = {}
        for member in members:
            md5_sum = hashlib.md5()
            md5_sum.update(member)
            ring[md5_sum.hexdigest().encode()] = member
        return ring

    def _get_my_resources(self, children):
        ring = CentralAgent._get_ring(children)
        hash_members = ring.keys()
        hash_members.sort()

        my_resources = []
        for resource in os_resources:
            hash_resource = os_resources_hash[resource]
            member_index = bisect.bisect(hash_members, hash_resource) % len(hash_members)
            hash_member = hash_members[member_index]
            member = ring[hash_member]

            if member == self._my_id:
                my_resources.append(resource)
        return my_resources

    def _my_watcher(self, event):
        """Kazoo watcher for membership events."""
        if event.type == 'CHILD':
            my_watcher = functools.partial(self._my_watcher)
            children = self._my_client.get_children("/central_team", watch=my_watcher)
            print("Central team members: %s" % children)
            self._my_resources = self._get_my_resources(children)
            print("My resources: %s" % self._my_resources)

    def _setup(self):
        """Ensure the central team group is created."""
        self._my_client.start(timeout=5)
        # Ensure that the "/central_team" znode is created.
        self._my_client.ensure_path("/central_team")

    def start(self):
        """Main loop for sending periodically the poll requests."""
        self._setup()

        self._my_client.create("/central_team/%s" % self._my_id, ephemeral=True)
        my_watcher = functools.partial(self._my_watcher)
        children = self._my_client.get_children("/central_team", watch=my_watcher)
        print("Central team members: %s" % children)

        self._my_resources = self._get_my_resources(children)
        print("My resources: %s" % self._my_resources)

        while True:
            for resource in self._my_resources:
                self.poll_resource(resource)
            time.sleep(3)

if __name__ == '__main__':
    central_agent = CentralAgent()
    central_agent.start()

