import glob
import os
import subprocess
from distutils.command.clean import clean

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext

try:
    from Cython.Build import cythonize
except ImportError:
    def cythonize(*args, **kwargs):
        from Cython.Build import cythonize
        return cythonize(*args, **kwargs)

with open("README.md", "r") as fh:
    long_description = fh.read()


AIOZYRE_PATH = os.path.dirname(os.path.abspath(__file__))

LIBS = (
    ('modules/libzmq', [
        ['./autogen.sh'],
        ['./configure', '--enable-shared', '--disable-static', '--with-docs=no', ''],
        ['make'],
    ]),
    ('modules/czmq', [
        ['./autogen.sh'],
        ['./configure', '--enable-shared', '--disable-static', '--with-docs=no', '--without-makecert'],
        ['make'],
    ]),
    ('modules/zyre', [
        ['./autogen.sh'],
        ['./configure', '--enable-shared', '--disable-static', '--with-docs=no'],
        ['make'],
    ]),
)


EXTRA_COMPILE_ARGS = [
    # '-g', '-O0'  # Uncomment for debugging
]


INCLUDE_DIRS = [
    'modules/libzmq/include',
    'modules/czmq/include',
    'modules/zyre/include',
]

LIBRARY_DIRS = [
    'modules/libzmq/src/.libs/',
    'modules/czmq/src/.libs/',
    'modules/zyre/src/.libs/',
]

LIBRARIES = ['zmq', 'czmq', 'zyre']


EXTENSION_CONFIG = dict(
    extra_compile_args=EXTRA_COMPILE_ARGS,
    include_dirs=INCLUDE_DIRS,
    # library_dirs=LIBRARY_DIRS,
    # libraries=LIBRARIES
)


class BuildExt(build_ext):
    def run(self):
        env = os.environ.copy()
        extra_cflags = ' -g -O0 -I{p}/modules/libzmq/include' \
                       ' -I{p}/modules/czmq/include' \
                       ' -I{p}/modules/zyre/include'.format(p=AIOZYRE_PATH)

        original_cppflags = os.environ.get('CPPFLAGS') or ''
        env['CPPFLAGS'] = extra_cflags + original_cppflags

        original_cflags = os.environ.get('CFLAGS') or ''
        env['CFLAGS'] = extra_cflags + original_cflags

        extra_ld_flags = ' -g -O0 -L{p}/modules/libzmq/src/.libs' \
                         ' -L{p}/modules/czmq/src/.libs' \
                         ' -L{p}/modules/zyre/src/.libs'.format(p=AIOZYRE_PATH)

        original_ldflags = os.environ.get('LDFLAGS') or ''
        env['LDFLAGS'] = extra_ld_flags + original_ldflags

        for cwd, cmds in LIBS:
            for cmd in cmds:
                print(cmd)
                #subprocess.check_call(cmd, cwd=cwd, env=env)

        # Sanity check that no unknown objects were added
        assert EXTRA_OBJECTs == get_extra_objects()
        build_ext.run(self)


class Clean(clean):
    def run(self):
        cmd = ['make', 'clean']
        for cwd, _ in LIBS:
            try:
                print(cmd)
                # subprocess.check_call(cmd, cwd=cwd)
            except:
                pass
        clean.run(self)


EXTRA_OBJECTs = [
    'modules/libzmq/src/.libs/libzmq_la-address.o',
    'modules/libzmq/src/.libs/libzmq_la-client.o',
    'modules/libzmq/src/.libs/libzmq_la-clock.o',
    'modules/libzmq/src/.libs/libzmq_la-ctx.o',
    'modules/libzmq/src/.libs/libzmq_la-curve_client.o',
    'modules/libzmq/src/.libs/libzmq_la-curve_mechanism_base.o',
    'modules/libzmq/src/.libs/libzmq_la-curve_server.o',
    'modules/libzmq/src/.libs/libzmq_la-dealer.o',
    'modules/libzmq/src/.libs/libzmq_la-devpoll.o',
    'modules/libzmq/src/.libs/libzmq_la-dgram.o',
    'modules/libzmq/src/.libs/libzmq_la-dish.o',
    'modules/libzmq/src/.libs/libzmq_la-dist.o',
    'modules/libzmq/src/.libs/libzmq_la-endpoint.o',
    'modules/libzmq/src/.libs/libzmq_la-epoll.o',
    'modules/libzmq/src/.libs/libzmq_la-err.o',
    'modules/libzmq/src/.libs/libzmq_la-fq.o',
    'modules/libzmq/src/.libs/libzmq_la-gather.o',
    'modules/libzmq/src/.libs/libzmq_la-gssapi_mechanism_base.o',
    'modules/libzmq/src/.libs/libzmq_la-gssapi_client.o',
    'modules/libzmq/src/.libs/libzmq_la-gssapi_server.o',
    'modules/libzmq/src/.libs/libzmq_la-io_object.o',
    'modules/libzmq/src/.libs/libzmq_la-io_thread.o',
    'modules/libzmq/src/.libs/libzmq_la-ip.o',
    'modules/libzmq/src/.libs/libzmq_la-ip_resolver.o',
    'modules/libzmq/src/.libs/libzmq_la-ipc_address.o',
    'modules/libzmq/src/.libs/libzmq_la-ipc_connecter.o',
    'modules/libzmq/src/.libs/libzmq_la-ipc_listener.o',
    'modules/libzmq/src/.libs/libzmq_la-kqueue.o',
    'modules/libzmq/src/.libs/libzmq_la-lb.o',
    'modules/libzmq/src/.libs/libzmq_la-mailbox.o',
    'modules/libzmq/src/.libs/libzmq_la-mailbox_safe.o',
    'modules/libzmq/src/.libs/libzmq_la-mechanism.o',
    'modules/libzmq/src/.libs/libzmq_la-mechanism_base.o',
    'modules/libzmq/src/.libs/libzmq_la-metadata.o',
    'modules/libzmq/src/.libs/libzmq_la-msg.o',
    'modules/libzmq/src/.libs/libzmq_la-mtrie.o',
    'modules/libzmq/src/.libs/libzmq_la-norm_engine.o',
    'modules/libzmq/src/.libs/libzmq_la-null_mechanism.o',
    'modules/libzmq/src/.libs/libzmq_la-object.o',
    'modules/libzmq/src/.libs/libzmq_la-options.o',
    'modules/libzmq/src/.libs/libzmq_la-own.o',
    'modules/libzmq/src/.libs/libzmq_la-pair.o',
    'modules/libzmq/src/.libs/libzmq_la-pgm_receiver.o',
    'modules/libzmq/src/.libs/libzmq_la-pgm_sender.o',
    'modules/libzmq/src/.libs/libzmq_la-pgm_socket.o',
    'modules/libzmq/src/.libs/libzmq_la-pipe.o',
    'modules/libzmq/src/.libs/libzmq_la-plain_client.o',
    'modules/libzmq/src/.libs/libzmq_la-plain_server.o',
    'modules/libzmq/src/.libs/libzmq_la-poll.o',
    'modules/libzmq/src/.libs/libzmq_la-poller_base.o',
    'modules/libzmq/src/.libs/libzmq_la-polling_util.o',
    'modules/libzmq/src/.libs/libzmq_la-pollset.o',
    'modules/libzmq/src/.libs/libzmq_la-precompiled.o',
    'modules/libzmq/src/.libs/libzmq_la-proxy.o',
    'modules/libzmq/src/.libs/libzmq_la-pub.o',
    'modules/libzmq/src/.libs/libzmq_la-pull.o',
    'modules/libzmq/src/.libs/libzmq_la-push.o',
    'modules/libzmq/src/.libs/libzmq_la-radio.o',
    'modules/libzmq/src/.libs/libzmq_la-radix_tree.o',
    'modules/libzmq/src/.libs/libzmq_la-random.o',
    'modules/libzmq/src/.libs/libzmq_la-raw_decoder.o',
    'modules/libzmq/src/.libs/libzmq_la-raw_encoder.o',
    'modules/libzmq/src/.libs/libzmq_la-raw_engine.o',
    'modules/libzmq/src/.libs/libzmq_la-reaper.o',
    'modules/libzmq/src/.libs/libzmq_la-rep.o',
    'modules/libzmq/src/.libs/libzmq_la-req.o',
    'modules/libzmq/src/.libs/libzmq_la-router.o',
    'modules/libzmq/src/.libs/libzmq_la-scatter.o',
    'modules/libzmq/src/.libs/libzmq_la-select.o',
    'modules/libzmq/src/.libs/libzmq_la-server.o',
    'modules/libzmq/src/.libs/libzmq_la-session_base.o',
    'modules/libzmq/src/.libs/libzmq_la-signaler.o',
    'modules/libzmq/src/.libs/libzmq_la-socket_base.o',
    'modules/libzmq/src/.libs/libzmq_la-socks.o',
    'modules/libzmq/src/.libs/libzmq_la-socks_connecter.o',
    'modules/libzmq/src/.libs/libzmq_la-stream.o',
    'modules/libzmq/src/.libs/libzmq_la-stream_connecter_base.o',
    'modules/libzmq/src/.libs/libzmq_la-stream_listener_base.o',
    'modules/libzmq/src/.libs/libzmq_la-stream_engine_base.o',
    'modules/libzmq/src/.libs/libzmq_la-sub.o',
    'modules/libzmq/src/.libs/libzmq_la-tcp.o',
    'modules/libzmq/src/.libs/libzmq_la-tcp_address.o',
    'modules/libzmq/src/.libs/libzmq_la-tcp_connecter.o',
    'modules/libzmq/src/.libs/libzmq_la-tcp_listener.o',
    'modules/libzmq/src/.libs/libzmq_la-thread.o',
    'modules/libzmq/src/.libs/libzmq_la-timers.o',
    'modules/libzmq/src/.libs/libzmq_la-tipc_address.o',
    'modules/libzmq/src/.libs/libzmq_la-tipc_connecter.o',
    'modules/libzmq/src/.libs/libzmq_la-tipc_listener.o',
    'modules/libzmq/src/.libs/libzmq_la-trie.o',
    'modules/libzmq/src/.libs/libzmq_la-udp_address.o',
    'modules/libzmq/src/.libs/libzmq_la-udp_engine.o',
    'modules/libzmq/src/.libs/libzmq_la-v1_decoder.o',
    'modules/libzmq/src/.libs/libzmq_la-v2_decoder.o',
    'modules/libzmq/src/.libs/libzmq_la-v1_encoder.o',
    'modules/libzmq/src/.libs/libzmq_la-v2_encoder.o',
    'modules/libzmq/src/.libs/libzmq_la-vmci.o',
    'modules/libzmq/src/.libs/libzmq_la-vmci_address.o',
    'modules/libzmq/src/.libs/libzmq_la-vmci_connecter.o',
    'modules/libzmq/src/.libs/libzmq_la-vmci_listener.o',
    'modules/libzmq/src/.libs/libzmq_la-xpub.o',
    'modules/libzmq/src/.libs/libzmq_la-xsub.o',
    'modules/libzmq/src/.libs/libzmq_la-zmq.o',
    'modules/libzmq/src/.libs/libzmq_la-zmq_utils.o',
    'modules/libzmq/src/.libs/libzmq_la-decoder_allocators.o',
    'modules/libzmq/src/.libs/libzmq_la-socket_poller.o',
    'modules/libzmq/src/.libs/libzmq_la-zap_client.o',
    'modules/libzmq/src/.libs/libzmq_la-zmtp_engine.o',
    'modules/libzmq/src/.libs/libzmq_la-tweetnacl.o',
    'modules/libzmq/src/.libs/libzmq_la-ws_address.o',
    'modules/libzmq/src/.libs/libzmq_la-wss_address.o',
    'modules/libzmq/src/.libs/libzmq_la-ws_connecter.o',
    'modules/libzmq/src/.libs/libzmq_la-ws_decoder.o',
    'modules/libzmq/src/.libs/libzmq_la-ws_encoder.o',
    'modules/libzmq/src/.libs/libzmq_la-ws_engine.o',
    'modules/libzmq/src/.libs/libzmq_la-ws_listener.o',
    'modules/czmq/src/.libs/libczmq_la-zactor.o',
    'modules/czmq/src/.libs/libczmq_la-zarmour.o',
    'modules/czmq/src/.libs/libczmq_la-zcert.o',
    'modules/czmq/src/.libs/libczmq_la-zcertstore.o',
    'modules/czmq/src/.libs/libczmq_la-zchunk.o',
    'modules/czmq/src/.libs/libczmq_la-zclock.o',
    'modules/czmq/src/.libs/libczmq_la-zconfig.o',
    'modules/czmq/src/.libs/libczmq_la-zdigest.o',
    'modules/czmq/src/.libs/libczmq_la-zdir.o',
    'modules/czmq/src/.libs/libczmq_la-zdir_patch.o',
    'modules/czmq/src/.libs/libczmq_la-zfile.o',
    'modules/czmq/src/.libs/libczmq_la-zframe.o',
    'modules/czmq/src/.libs/libczmq_la-zhash.o',
    'modules/czmq/src/.libs/libczmq_la-zhashx.o',
    'modules/czmq/src/.libs/libczmq_la-ziflist.o',
    'modules/czmq/src/.libs/libczmq_la-zlist.o',
    'modules/czmq/src/.libs/libczmq_la-zlistx.o',
    'modules/czmq/src/.libs/libczmq_la-zloop.o',
    'modules/czmq/src/.libs/libczmq_la-zmsg.o',
    'modules/czmq/src/.libs/libczmq_la-zpoller.o',
    'modules/czmq/src/.libs/libczmq_la-zsock.o',
    'modules/czmq/src/.libs/libczmq_la-zstr.o',
    'modules/czmq/src/.libs/libczmq_la-zsys.o',
    'modules/czmq/src/.libs/libczmq_la-zuuid.o',
    'modules/czmq/src/.libs/libczmq_la-zauth.o',
    'modules/czmq/src/.libs/libczmq_la-zbeacon.o',
    'modules/czmq/src/.libs/libczmq_la-zgossip.o',
    'modules/czmq/src/.libs/libczmq_la-zmonitor.o',
    'modules/czmq/src/.libs/libczmq_la-zproxy.o',
    'modules/czmq/src/.libs/libczmq_la-zrex.o',
    'modules/czmq/src/.libs/libczmq_la-zgossip_msg.o',
    'modules/czmq/src/.libs/libczmq_la-zargs.o',
    'modules/czmq/src/.libs/libczmq_la-zproc.o',
    'modules/czmq/src/.libs/libczmq_la-ztimerset.o',
    'modules/czmq/src/.libs/libczmq_la-ztrie.o',
    'modules/czmq/src/.libs/libczmq_la-zhttp_client.o',
    'modules/czmq/src/.libs/libczmq_la-zhttp_server.o',
    'modules/czmq/src/.libs/libczmq_la-zhttp_server_options.o',
    'modules/czmq/src/.libs/libczmq_la-zhttp_request.o',
    'modules/czmq/src/.libs/libczmq_la-zhttp_response.o',
    'modules/czmq/src/.libs/libczmq_la-czmq_private_selftest.o',
    'modules/zyre/src/.libs/libzyre_la-zyre.o',
    'modules/zyre/src/.libs/libzyre_la-zyre_event.o',
    'modules/zyre/src/.libs/libzyre_la-zre_msg.o',
    'modules/zyre/src/.libs/libzyre_la-zyre_peer.o',
    'modules/zyre/src/.libs/libzyre_la-zyre_group.o',
    'modules/zyre/src/.libs/libzyre_la-zyre_election.o',
    'modules/zyre/src/.libs/libzyre_la-zyre_node.o',
    'modules/zyre/src/.libs/libzyre_la-zyre_private_selftest.o'
]


def get_extra_objects():
    all_objs = []
    for d in LIBRARY_DIRS:
        objs = glob.glob(os.path.join(d, '*.o'))
        all_objs += sorted(objs, key=os.path.getmtime)
    return all_objs


setup(
    name='aiozyre',
    version='1.0.0',
    description='asyncio-friendly Python bindings for Zyre',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Elijah Shaw-Rutschman',
    author_email='elijahr+aiozyre@gmail.com',
    packages=['aiozyre'],
    setup_requires=[
        'cython',
    ],
    cmdclass={
        'build_ext': BuildExt,
        'clean': Clean,
    },
    ext_modules=cythonize([
        Extension(
            'aiozyre.zyre',
            sources=['aiozyre/zyre.pyx'],
            extra_objects=EXTRA_OBJECTs,
            extra_link_args=['-lcurl'],
            **EXTENSION_CONFIG
        ),
        Extension(
            'aiozyre.actor',
            sources=['aiozyre/actor.pyx'],
            **EXTENSION_CONFIG
        ),
        Extension(
            'aiozyre.futures',
            sources=['aiozyre/futures.pyx'],
            **EXTENSION_CONFIG
        ),
        Extension(
            'aiozyre.node',
            sources=['aiozyre/node.pyx'],
            **EXTENSION_CONFIG
        ),
        Extension(
            'aiozyre.nodeconfig',
            sources=['aiozyre/nodeconfig.pyx'],
            **EXTENSION_CONFIG
        ),
        Extension(
            'aiozyre.signals',
            sources=['aiozyre/signals.pyx'],
            # **EXTENSION_CONFIG
        ),
        Extension(
            'aiozyre.util',
            sources=['aiozyre/util.pyx'],
            **EXTENSION_CONFIG
        ),
    ], gdb_debug=True),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3',
        'Topic :: System :: Networking',
        'Framework :: AsyncIO',
    ],
)
