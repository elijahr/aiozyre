#!/usr/bin/env python -W ignore::DeprecationWarning

import argparse
import asyncio
import sys

from aioconsole import ainput
from aiozyre import Node, Stopped
from blessed import Terminal

term = Terminal()

HELP = '''Commands are:

{t.bold}/help{t.normal}      print this help message
{t.bold}/leave{t.normal}     leave the room and exit

'''.format(t=term)


class Chatter:
    def __init__(self, username):
        self.node = Node(username, groups=['chatter'])

    @property
    def username(self):
        return self.node.name

    @property
    def prompt(self):
        return '{t.bold}{username}{t.normal}: '.format(t=term, username=self.username)

    def out(self, output, prompt=True, flush=True):
        output += '\n'
        if prompt:
            output += self.prompt
        # delete the prompt
        output = ('\b \b' * len(self.prompt)) + output
        sys.stdout.write(output)
        if flush:
            sys.stdout.flush()

    async def talk(self):
        await self.node.start()
        sys.stdout.write(
            '\n{t.bold}Welcome to the chatroom, {username}.{t.normal} '
            'Enter a message to chat. {HELP}'.format(t=term, username=self.username, HELP=HELP))

        while True:
            try:
                msg = await ainput(self.prompt)
            except EOFError:
                # Ctrl-D was pressed
                await self.leave()
                break
            else:
                if msg.startswith('/'):
                    # commands
                    if 'help' in msg:
                        sys.stdout.write(HELP)
                    elif 'leave' in msg:
                        await self.leave()
                        break
                    else:
                        self.out('Unknown command %s' % msg, prompt=False)
                else:
                    # shout message to the group
                    await self.node.shout('chatter', msg)

    async def listen(self):
        # Give the node some time to start
        await asyncio.sleep(1)
        while True:
            try:
                msg = await self.node.recv()
            except Stopped:
                break
            else:
                if msg.event == 'SHOUT':
                    self.out('{t.bold}{msg.name}{t.normal}: {msg.string}'.format(t=term, msg=msg), flush=False)
                elif msg.event == 'ENTER':
                    self.out('* %s is in the room' % msg.name)
                elif msg.event == 'LEAVE':
                    self.out('* %s has left the room' % msg.name)

    async def leave(self):
        self.out('* you left the room', prompt=False)
        await self.node.leave('chatter')
        await self.node.stop()

    def run(self):
        loop = asyncio.get_event_loop()
        tasks = asyncio.gather(
            loop.create_task(self.talk()),
            loop.create_task(self.listen()),
        )
        try:
            loop.run_until_complete(tasks)
        finally:
            loop.close()


def main():
    parser = argparse.ArgumentParser(description='Chat on the local network.')
    parser.add_argument('username', type=str, help='Your chat username')
    args = parser.parse_args()
    chatter = Chatter(args.username)
    chatter.run()


if __name__ == '__main__':
    main()
