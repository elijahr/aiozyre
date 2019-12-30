import faulthandler
from pprint import pformat

faulthandler.enable(all_threads=True)
import tracemalloc

tracemalloc.start()

import asyncio
import sys
import unittest

import uvloop


from aiozyre import Node, Stopped


class AIOZyreTestCase(unittest.TestCase):
    __slots__ = ('nodes', 'loop')

    def setUp(self):
        uvloop.install()
        self.nodes = {}
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def test_cluster(self):
        self.loop.run_until_complete(self.create_cluster())
        self.assert_received_message('soup', event='ENTER', name='salad')
        self.assert_received_message('soup', event='ENTER', name='lacroix')
        self.assert_received_message('soup', event='JOIN', name='salad', group='foods')
        self.assert_received_message('soup', event='JOIN', name='lacroix', group='drinks')
        self.assert_received_message('soup', event='SHOUT', name='salad', group='foods',
                                     blob=b'Hello foods from salad')
        self.assert_received_message('soup', event='SHOUT', name='lacroix', group='drinks',
                                     blob=b'Hello drinks from lacroix')

        self.assert_received_message('salad', event='ENTER', name='soup')
        self.assert_received_message('salad', event='ENTER', name='lacroix')
        self.assert_received_message('salad', event='JOIN', name='soup', group='foods')
        self.assert_received_message('salad', event='JOIN', name='soup', group='drinks')
        self.assert_received_message('salad', event='JOIN', name='lacroix', group='drinks')
        self.assert_received_message('salad', event='SHOUT', name='soup', group='foods',
                                     blob=b'Hello foods from soup')

        self.assert_received_message('lacroix', event='ENTER', name='salad')
        self.assert_received_message('lacroix', event='ENTER', name='soup')
        self.assert_received_message('lacroix', event='JOIN', name='salad', group='foods')
        self.assert_received_message('lacroix', event='JOIN', name='soup', group='drinks')
        self.assert_received_message('lacroix', event='JOIN', name='soup', group='foods')
        self.assert_received_message('lacroix', event='SHOUT', name='soup', group='drinks',
                                     blob=b'Hello drinks from soup')

        self.assertEqual(self.nodes['soup']['own_groups'], {'foods', 'drinks'})
        self.assertEqual(self.nodes['soup']['peer_groups'], {'foods', 'drinks'})
        self.assertEqual(len(self.nodes['soup']['peer_addresses']), 2)
        self.assertEqual(self.nodes['soup']['peer_header_value_types'], {'pamplemousse', 'caesar'})
        self.assertEqual(self.nodes['soup']['peers'], {self.nodes['salad']['uuid'], self.nodes['lacroix']['uuid']})
        self.assertEqual(self.nodes['soup']['peers_by_group'], {
            'foods': {self.nodes['salad']['uuid']},
            'drinks': {self.nodes['lacroix']['uuid']}
        })

        self.assertEqual(self.nodes['salad']['own_groups'], {'foods'})
        self.assertEqual(self.nodes['salad']['peer_groups'], {'foods', 'drinks'})
        self.assertEqual(len(self.nodes['salad']['peer_addresses']), 2)
        self.assertEqual(self.nodes['salad']['peer_header_value_types'], {'pamplemousse', 'tomato bisque'})
        self.assertEqual(self.nodes['salad']['peers'], {self.nodes['lacroix']['uuid'], self.nodes['soup']['uuid']})
        self.assertEqual(self.nodes['salad']['peers_by_group'], {
            'foods': {self.nodes['soup']['uuid']},
            'drinks': {self.nodes['lacroix']['uuid'], self.nodes['soup']['uuid']}
        })

        self.assertEqual(self.nodes['lacroix']['own_groups'], {'drinks'})
        self.assertEqual(self.nodes['lacroix']['peer_groups'], {'foods', 'drinks'})
        self.assertEqual(len(self.nodes['lacroix']['peer_addresses']), 2)
        self.assertEqual(self.nodes['lacroix']['peer_header_value_types'], {'tomato bisque', 'caesar'})
        self.assertEqual(self.nodes['lacroix']['peers'], {self.nodes['salad']['uuid'], self.nodes['soup']['uuid']})
        self.assertEqual(self.nodes['lacroix']['peers_by_group'], {
            'foods': {self.nodes['salad']['uuid'], self.nodes['soup']['uuid']},
            'drinks': {self.nodes['soup']['uuid']}
        })

    def test_start_stop(self):
        self.loop.run_until_complete(self.start_stop())
        self.assert_received_message('fuzz', blob=b'Hello from buzz')

    async def start_stop(self):
        fuzz = await self.start('fuzz', groups=['test'])
        buzz = await self.start('buzz', groups=['test'])
        await fuzz.stop()
        await fuzz.start()
        self.create_task(self.listen(fuzz))
        await buzz.whisper(fuzz.uuid, b'Hello from buzz')
        await asyncio.sleep(1)

    def assert_received_message(self, node_name, **kwargs):
        match = False
        for msg in self.nodes[node_name]['messages']:
            if set(kwargs.items()).issubset(set(msg.to_dict().items())):
                match = True
                break
        self.assertTrue(match, '%s not in %s' % (pformat(kwargs), pformat(self.nodes[node_name]['messages'])))

    async def create_cluster(self):
        print('Starting nodes...')
        await self.start('soup', groups=['foods', 'drinks'], headers={'type': 'tomato bisque'})
        await self.start('salad', groups=['foods'], headers={'type': 'caesar'})
        await self.start('lacroix', groups=['drinks'], headers={'type': 'pamplemousse'})

        print('Setting up listeners...')
        for node_info in self.nodes.values():
            # Intentionally don't wait for these, they stop themselves
            self.create_task(self.listen(node_info['node']))

        print('Sending messages...')
        await asyncio.wait([
            self.create_task(self.nodes['soup']['node'].shout('drinks', b'Hello drinks from soup')),
            self.create_task(self.nodes['soup']['node'].shout('foods', b'Hello foods from soup')),
            self.create_task(self.nodes['salad']['node'].shout('foods', b'Hello foods from salad')),
            self.create_task(self.nodes['lacroix']['node'].shout('drinks', b'Hello drinks from lacroix')),
        ])

        print('Collecting peer data...')
        await asyncio.wait([
            self.create_task(self.collect_peer_info('soup')),
            self.create_task(self.collect_peer_info('salad')),
            self.create_task(self.collect_peer_info('lacroix')),
        ])

        # Give nodes some time to receive the messages
        print('Receiving messages...')
        await asyncio.sleep(1)

    async def start(self, name, groups=None, headers=None) -> Node:
        node = Node(
            name, groups=groups, headers=headers, endpoint='inproc://{}'.format(name),
            gossip_endpoint='inproc://gossip-hub', verbose=True, evasive_timeout_ms=30000,
            expired_timeout_ms=30000,
        )
        await node.start()
        self.nodes[node.name] = {'node': node, 'messages': [], 'uuid': node.uuid}
        self.addCleanup(self.stop, node)
        return node

    def stop(self, node):
        print('Stopping %s' % node)
        self.loop.run_until_complete(node.stop())

    async def listen(self, node):
        name = node.name
        while node.running:
            try:
                msg = await node.recv()
            except Stopped:
                break
            else:
                self.nodes[name]['messages'].append(msg)

    async def collect_peer_info(self, name):
        node = self.nodes[name]['node']

        self.nodes[name]['peer_addresses'] = peer_addresses = set()
        for peer in self.nodes.values():
            if peer['node'].name != name:
                peer_addresses.add(await node.peer_address(peer['node'].uuid))

        self.nodes[name]['peer_header_value_types'] = peer_header_value_types = set()
        for peer in self.nodes.values():
            if peer['node'].name != name:
                peer_header_value_types.add(await node.peer_header_value(peer['node'].uuid, 'type'))

        self.nodes[name]['peers'] = await node.peers()
        self.nodes[name]['peer_groups'] = await node.peer_groups()
        self.nodes[name]['own_groups'] = await node.own_groups()

        self.nodes[name]['peers_by_group'] = peers_by_group = {}
        for group in {'drinks', 'foods'}:
            peers_by_group[group] = await node.peers_by_group(group)

    def create_task(self, coro):
        if sys.version_info[:2] >= (3, 8):
            return asyncio.create_task(coro)
        else:
            return self.loop.create_task(coro)


if __name__ == '__main__':
    unittest.main()
