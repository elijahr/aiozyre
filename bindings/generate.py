import os

import pybindgen
from pybindgen import retval, param

from cfuncs import header, _wrap_zmq_getsockopt_int, _wrap_zmq_setsockopt_int, \
    _wrap_zpoller_wait, _wrap_zyre_peers, _wrap_zyre_own_groups, _wrap_zyre_peer_groups, _wrap_zyre_peers_by_group, \
    _wrap_zpoller_new, _wrap_zsys_interrupted
from utils import PtrPtrFreeFunctionPolicy, Unformat


class XZyreModule(pybindgen.Module):
    def __init__(self):
        super(XZyreModule, self).__init__('xzyre')
        self.add_include('<stdarg.h>')
        self.add_include('"zyre.h"')
        self.header.writeln('typedef char PYBYTE;')
        self.header.writeln(header)

        # self.add_zmq()
        self.add_zsock()
        self.add_zpoller()
        self.add_zmsg()
        # self.add_zlist()
        # self.add_zactor()
        self.add_zyre()

    # def add_zmq(self):
    #     self.add_custom_function_wrapper(
    #         'zmq_getsockopt_int',
    #         '_wrap_zmq_getsockopt_int',
    #         _wrap_zmq_getsockopt_int
    #     )
    #     self.add_custom_function_wrapper(
    #         'zmq_setsockopt_int',
    #         '_wrap_zmq_setsockopt_int',
    #         _wrap_zmq_setsockopt_int
    #     )
    #     self.add_custom_function_wrapper(
    #         'get_zsys_interrupted',
    #         '_wrap_zsys_interrupted',
    #         _wrap_zsys_interrupted
    #     )
    #     self.add_enum(
    #         'ZMQ',
    #         (
    #             ('ZMQ_RCVTIMEO', 'ZMQ_RCVTIMEO'),
    #             ('ZMQ_SNDTIMEO', 'ZMQ_SNDTIMEO'),
    #         )
    #     )

    # def add_zactor(self):
    #     zactor_t = self.add_struct(
    #         'zactor_t',
    #         no_constructor=True,
    #         no_copy=True,
    #         memory_policy=PtrPtrFreeFunctionPolicy('zactor_destroy'))
    #     self.add_typedef(zactor_t, '_zactor_t')
    #     self.add_custom_function_wrapper('zactor_new', '_wrap_zactor_new',
    #                                      _wrap_zactor_new)

    def add_zpoller(self):
        zpoller_t = self.add_struct(
            'zpoller_t',
            no_constructor=True,
            no_copy=True,
            memory_policy=PtrPtrFreeFunctionPolicy('zpoller_destroy')
        )
        self.add_typedef(zpoller_t, '_zpoller_t')
        self.add_function(
            'zpoller_new',
            retval('zpoller_t*', caller_owns_return=True),
            [
                param('NULL', 'NULL')
            ]
        )
        self.add_function(
            'zpoller_add',
            retval('int'),
            [
                param('zpoller_t*', 'self', transfer_ownership=False),
                param('zsock_t*', 'reader', transfer_ownership=False)
            ]
        )
        self.add_custom_function_wrapper(
            'zpoller_wait', '_wrap_zpoller_wait', _wrap_zpoller_wait
        )
        self.add_function(
            'zpoller_expired',
            retval('bool'),
            [
                param('zpoller_t*', 'self', transfer_ownership=False),
            ]
        )

    def add_zmsg(self):
        zmsg_t = self.add_struct(
            'zmsg_t',
            no_constructor=True,
            no_copy=True,
            memory_policy=PtrPtrFreeFunctionPolicy('zmsg_destroy')
        )
        self.add_typedef(zmsg_t, '_zmsg_t')
        self.add_function(
            'zmsg_new', retval('zmsg_t*', caller_owns_return=True), []
        )
        self.add_function(
            'zmsg_popstr',
            retval('char*'),
            [param('zmsg_t*', 'self', transfer_ownership=False)]
        )
        self.add_function(
            'zmsg_popstr',
            retval('PYBYTE*'),
            [param('zmsg_t*', 'self', transfer_ownership=False)],
            custom_name='zmsg_popbytes'
        )
        self.add_function(
            'zmsg_pushstr',
            retval('int'),
            [
                param('zmsg_t*', 'self', transfer_ownership=False),
                param('const char*', 'string'),
            ]
        )
        self.add_function(
            'zmsg_pushstr',
            retval('int'),
            [
                param('zmsg_t*', 'self', transfer_ownership=False),
                param('const PYBYTE*', 'string'),
            ],
            custom_name='zmsg_pushbytes'
        )

    # def add_zlist(self):
    #     zlist_t = self.add_struct(
    #         'zlist_t',
    #         no_constructor=True,
    #         no_copy=True,
    #         memory_policy=PtrPtrFreeFunctionPolicy('zlist_destroy'))
    #     self.add_typedef(zlist_t, '_zlist_t')

    def add_zsock(self):
        zsock_t = self.add_struct(
            'zsock_t',
            no_constructor=True,
            no_copy=True,
        )
        self.add_typedef(zsock_t, '_zsock_t')

    def add_zyre(self):
        zyre_t = self.add_struct(
            'zyre_t',
            no_constructor=True,
            no_copy=True,
            memory_policy=PtrPtrFreeFunctionPolicy('zyre_destroy')
        )
        self.add_typedef(zyre_t, '_zyre_t')
        self.add_function(
            'zyre_new',
            retval('zyre_t*', caller_owns_return=True),
            [param('char*', 'name')]
        )

        self.add_function(
            'zyre_uuid',
            retval('const char*'),
            [param('zyre_t*', 'self', transfer_ownership=False)]
        )

        self.add_function(
            'zyre_name',
            retval('const char*'),
            [param('zyre_t*', 'self', transfer_ownership=False)]
        )

        self.add_function(
            'zyre_set_header',
            retval('void'),
            [
                param('zyre_t*', 'self', transfer_ownership=False),
                param('char*', 'name'),
                Unformat('char*', 'value')
            ],
            unblock_threads=True
        )
        # self.add_function(
        #     'zyre_set_verbose',
        #     retval('void'),
        #     [param('zyre_t*', 'self', transfer_ownership=False)]
        # )

        # self.add_function(
        #     'zyre_set_port',
        #     retval('void'),
        #     [
        #         param('zyre_t*', 'self', transfer_ownership=False),
        #         param('int', 'port_nbr')
        #     ]
        # )

        self.add_function(
            'zyre_set_evasive_timeout',
            retval('void'),
            [
                param('zyre_t*', 'self', transfer_ownership=False),
                param('int', 'interval')
            ]
        )

        self.add_function(
            'zyre_set_expired_timeout',
            retval('void'),
            [
                param('zyre_t*', 'self', transfer_ownership=False),
                param('int', 'interval')
            ]
        )

        self.add_function(
            'zyre_set_interval',
            retval('void'),
            [
                param('zyre_t*', 'self', transfer_ownership=False),
                param('int', 'interval')
            ]
        )

        # self.add_function(
        #     'zyre_set_interface',
        #     retval('void'),
        #     [
        #         param('zyre_t*', 'self', transfer_ownership=False),
        #         param('char*', 'value')
        #     ]
        # )
        #
        # self.add_function(
        #     'zyre_set_endpoint',
        #     retval('int'),
        #     [
        #         param('zyre_t*', 'self', transfer_ownership=False),
        #         Unformat('char*', 'value')
        #     ]
        # )

        # self.add_function(
        #     'zyre_gossip_bind',
        #     retval('void'),
        #     [
        #         param('zyre_t*', 'self', transfer_ownership=False),
        #         Unformat('char*', 'value')
        #     ],
        #     unblock_threads=True
        # )
        #
        # self.add_function(
        #     'zyre_gossip_connect',
        #     retval('void'),
        #     [
        #         param('zyre_t*', 'self', transfer_ownership=False),
        #         Unformat('char*', 'value')
        #     ],
        #     unblock_threads=True
        # )

        self.add_function(
            'zyre_start',
            retval('int'),
            [param('zyre_t*', 'self', transfer_ownership=False)],
            unblock_threads=True
        )

        self.add_function(
            'zyre_stop',
            retval('void'),
            [param('zyre_t*', 'self', transfer_ownership=False)],
            unblock_threads=True
        )
        self.add_function(
            'zyre_join',
            retval('int'),
            [
                param('zyre_t*', 'self', transfer_ownership=False),
                param('char*', 'group')
            ],
            unblock_threads=True
        )
        self.add_function(
            'zyre_leave',
            retval('int'),
            [
                param('zyre_t*', 'self', transfer_ownership=False),
                param('char*', 'group')
            ],
            unblock_threads=True
        )
        self.add_function(
            'zyre_recv',
            retval('zmsg_t*', caller_owns_return=True),
            [param('zyre_t*', 'self', transfer_ownership=False)],
            unblock_threads=True
        )
        self.add_function(
            'zyre_whisper',
            retval('int'),
            [
                param('zyre_t*', 'self', transfer_ownership=False),
                param('char*', 'peer'),
                param('zmsg_t**', 'msg')
            ],
            unblock_threads=True
        )
        self.add_function(
            'zyre_shout',
            retval('int'),
            [
                param('zyre_t*', 'self', transfer_ownership=False),
                param('char*', 'group'),
                param('zmsg_t**', 'msg')
            ],
            unblock_threads=True
        )
        self.add_function(
            'zyre_whispers',
            retval('int'),
            [
                param('zyre_t*', 'self', transfer_ownership=False),
                param('char*', 'peer'),
                Unformat('char*', 'msg')
            ],
            unblock_threads=True
        )
        self.add_function(
            'zyre_shouts',
            retval('int'),
            [
                param('zyre_t*', 'self', transfer_ownership=False),
                param('char*', 'group'),
                Unformat('char*', 'msg')
            ],
            unblock_threads=True
        )
        self.add_custom_function_wrapper(
            'zyre_peers', '_wrap_zyre_peers', _wrap_zyre_peers
        )
        self.add_custom_function_wrapper(
            'zyre_own_groups', '_wrap_zyre_own_groups', _wrap_zyre_own_groups
        )
        self.add_custom_function_wrapper(
            'zyre_peer_groups',
            '_wrap_zyre_peer_groups',
            _wrap_zyre_peer_groups
        )
        self.add_custom_function_wrapper(
            'zyre_peers_by_group',
            '_wrap_zyre_peers_by_group',
            _wrap_zyre_peers_by_group
        )
        self.add_function(
            'zyre_peer_address',
            retval('char*'),
            [
                param('zyre_t*', 'self', transfer_ownership=False),
                param('char*', 'peer')
            ],
            unblock_threads=True
        )
        self.add_function(
            'zyre_peer_header_value',
            retval('char*'),
            [
                param('zyre_t*', 'self', transfer_ownership=False),
                param('char*', 'peer'),
                param('char*', 'name')
            ],
            unblock_threads=True
        )
        self.add_function(
            'zyre_socket',
            retval('zsock_t*', caller_owns_return=False, reference_existing_object=True, caller_manages_return=False),
            [param('zyre_t*', 'self', transfer_ownership=False)],
            unblock_threads=True
        )
        # self.add_function(
        #     'zyre_print',
        #     retval('void'),
        #     [param('zyre_t*', 'self', transfer_ownership=False)]
        # )
        self.add_function('zyre_version', retval('uint64_t'), [])


def main():
    filename = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        '../src/aiozyre',
        'xzyre.cpp',
    ))
    with open(filename, 'wt') as f:
        xzyre_module = XZyreModule()
        xzyre_module.generate(f)
        print('Generated file {}'.format(filename))


if __name__ == '__main__':
    main()
