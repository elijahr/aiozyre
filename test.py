import faulthandler

faulthandler.enable(all_threads=True)

try:
    import tracemalloc
    tracemalloc.start()
except ImportError:
    # Not available in pypy
    pass

from pprint import pformat
import asyncio
import sys
import unittest

from aiozyre import Node, Stopped


class AIOZyreTestCase(unittest.TestCase):
    __slots__ = ('nodes', 'loop')

    def setUp(self):
        self.nodes = {}
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self) -> None:
        self.loop.close()

    def test_cluster(self):
        self.loop.run_until_complete(self.create_cluster())
        try:
            self.assert_received_message('soup', event='ENTER', name='salad')
        except AssertionError:
            self.assert_received_message('soup', event='ENTER', name='lacroix')
        self.assert_received_message('soup', event='JOIN', name='salad', group='foods')
        self.assert_received_message('soup', event='JOIN', name='lacroix', group='drinks')
        self.assert_received_message('soup', event='SHOUT', name='salad', group='foods',
                                     blob=b'Hello foods from salad')
        self.assert_received_message('soup', event='SHOUT', name='lacroix', group='drinks',
                                     blob=b'Hello drinks from lacroix')
        try:
            self.assert_received_message('salad', event='ENTER', name='soup')
        except AssertionError:
            self.assert_received_message('salad', event='ENTER', name='lacroix')
        self.assert_received_message('salad', event='JOIN', name='soup', group='foods')
        self.assert_received_message('salad', event='JOIN', name='soup', group='drinks')
        self.assert_received_message('salad', event='JOIN', name='lacroix', group='drinks')
        self.assert_received_message('salad', event='SHOUT', name='soup', group='foods',
                                     blob=b'Hello foods from soup')

        try:
            self.assert_received_message('lacroix', event='ENTER', name='salad')
        except AssertionError:
            self.assert_received_message('lacroix', event='ENTER', name='soup')
        self.assert_received_message('lacroix', event='JOIN', name='salad', group='foods')
        self.assert_received_message('lacroix', event='JOIN', name='soup', group='drinks')
        self.assert_received_message('lacroix', event='JOIN', name='soup', group='foods')
        self.assert_received_message('lacroix', event='SHOUT', name='soup', group='drinks',
                                     blob=b'Hello drinks from soup')

        self.assertEqual(self.nodes['soup']['own_groups'], {'foods', 'drinks'})
        self.assertEqual(self.nodes['soup']['peer_groups'], {'foods', 'drinks'})
        self.assertEqual(self.nodes['soup']['peer_header_value_types'], {'pamplemousse', 'caesar'})
        self.assertEqual(self.nodes['soup']['peers'], {self.nodes['salad']['uuid'], self.nodes['lacroix']['uuid']})
        self.assertEqual(self.nodes['soup']['peers_by_group'], {
            'foods': {self.nodes['salad']['uuid']},
            'drinks': {self.nodes['lacroix']['uuid']}
        })

        self.assertEqual(self.nodes['salad']['own_groups'], {'foods'})
        self.assertEqual(self.nodes['salad']['peer_groups'], {'foods', 'drinks'})
        self.assertEqual(self.nodes['salad']['peer_header_value_types'], {'pamplemousse', 'tomato bisque'})
        self.assertEqual(self.nodes['salad']['peers'], {self.nodes['lacroix']['uuid'], self.nodes['soup']['uuid']})
        self.assertEqual(self.nodes['salad']['peers_by_group'], {
            'foods': {self.nodes['soup']['uuid']},
            'drinks': {self.nodes['lacroix']['uuid'], self.nodes['soup']['uuid']}
        })

        self.assertEqual(self.nodes['lacroix']['own_groups'], {'drinks'})
        self.assertEqual(self.nodes['lacroix']['peer_groups'], {'foods', 'drinks'})
        self.assertEqual(self.nodes['lacroix']['peer_header_value_types'], {'tomato bisque', 'caesar'})
        self.assertEqual(self.nodes['lacroix']['peers'], {self.nodes['salad']['uuid'], self.nodes['soup']['uuid']})
        self.assertEqual(self.nodes['lacroix']['peers_by_group'], {
            'foods': {self.nodes['salad']['uuid'], self.nodes['soup']['uuid']},
            'drinks': {self.nodes['soup']['uuid']}
        })

    def test_start_stop(self):
        self.loop.run_until_complete(self.start_stop())
        self.assert_received_message('fizz', blob=b'Hello #1 from buzz')
        self.assert_received_message('fizz', blob=b'Hello #2 from buzz')

    def test_timeout(self):
        self.loop.run_until_complete(self.timeout())

    def assert_received_message(self, node_name, **kwargs):
        match = False
        for msg in self.nodes[node_name]['messages']:
            if set(kwargs.items()).issubset(set(msg.to_dict().items())):
                match = True
                break
        self.assertTrue(match, '%s not in %s' % (pformat(kwargs), pformat(self.nodes[node_name]['messages'])))

    async def create_cluster(self):
        print('Starting nodes...')
        soup = await self.start('soup', groups=['foods', 'drinks'], headers={'type': 'tomato bisque'})
        salad = await self.start('salad', groups=['foods'], headers={'type': 'caesar'})
        lacroix = await self.start('lacroix', groups=['drinks'], headers={'type': 'pamplemousse'})

        print('Setting up listeners...')
        self.listen(soup, salad, lacroix)

        print('Sending messages...')
        await asyncio.wait([
            self.create_task(soup.shout('drinks', b'Hello drinks from soup')),
            self.create_task(soup.shout('foods', b'Hello foods from soup')),
            self.create_task(salad.shout('foods', b'Hello foods from salad')),
            self.create_task(lacroix.shout('drinks', b'Hello drinks from lacroix')),
        ])

        print('Collecting peer data...')
        await asyncio.wait([
            self.create_task(self.collect_peer_info('soup')),
            self.create_task(self.collect_peer_info('salad')),
            self.create_task(self.collect_peer_info('lacroix')),
        ])

        from pprint import pprint
        pprint(self.nodes)

        # Give nodes some time to receive the messages
        print('Receiving messages...')
        await asyncio.sleep(5)

        print('Stopping nodes...')
        await asyncio.wait([
            self.create_task(self.nodes[node]['node'].stop())
            for node in self.nodes
        ])

    async def timeout(self):
        fizz = await self.start('fizz')
        try:
            with self.assertRaises(asyncio.TimeoutError):
                await fizz.recv(timeout=0)
        finally:
            await fizz.stop()

    async def start_stop(self):
        fizz = await self.start('fizz', groups=['test'])
        buzz = await self.start('buzz', groups=['test'])
        self.listen(fizz)
        await buzz.whisper(fizz.uuid, b'Hello #1 from buzz')
        # Give some time to receive messages
        await asyncio.sleep(3)
        await fizz.stop()
        await buzz.stop()

        # Restart and send a new message
        await fizz.start()
        await buzz.start()
        self.listen(fizz)
        await buzz.whisper(fizz.uuid, b'Hello #2 from buzz')
        # Give some time to receive messages
        await asyncio.sleep(3)
        await fizz.stop()
        await buzz.stop()

    async def start(self, name, groups=None, headers=None) -> Node:
        node = Node(
            name, groups=groups, headers=headers,
            endpoint='inproc://{}'.format(name),
            gossip_endpoint='inproc://gossip',
            verbose=True,
            evasive_timeout_ms=30000,
            expired_timeout_ms=30000,
        )
        await node.start()
        self.nodes[node.name] = {'node': node, 'messages': [], 'uuid': node.uuid}
        return node

    def listen(self, *nodes):
        for node in nodes:
            # Intentionally don't wait for these, they stop themselves
            self.create_task(self._listen(node))

    async def _listen(self, node):
        name = node.name
        print('Listener for %s started' % node.name)
        while True:
            try:
                msg = await node.recv()
            except Stopped:
                print('Listener for %s stopped' % node.name)
                break
            else:
                self.nodes[name]['messages'].append(msg)

    async def collect_peer_info(self, name):
        node = self.nodes[name]['node']

        print('Collecting peer header values "type"...')
        self.nodes[name]['peer_header_value_types'] = peer_header_value_types = set()
        for peer in self.nodes.values():
            if peer['node'].name != name:
                peer_header_value_types.add(await node.peer_header_value(peer['node'].uuid, 'type'))

        print('Collecting peers...')
        self.nodes[name]['peers'] = await node.peers()
        print('Collecting peer groups...')
        self.nodes[name]['peer_groups'] = await node.peer_groups()
        print('Collecting own groups...')
        self.nodes[name]['own_groups'] = await node.own_groups()

        print('Collecting peers by group...')
        self.nodes[name]['peers_by_group'] = peers_by_group = {}
        for group in {'drinks', 'foods'}:
            peers_by_group[group] = await node.peers_by_group(group)

        print('Collected peer data')

    def create_task(self, coro):
        if sys.version_info[:2] >= (3, 8):
            return asyncio.create_task(coro)
        else:
            return self.loop.create_task(coro)


if __name__ == '__main__':
    unittest.main()
