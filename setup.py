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
        ['./configure', '--enable-shared', '--disable-static', '--with-docs=no'],
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
        extra_cflags = ' -I{p}/modules/libzmq/include' \
                       ' -I{p}/modules/czmq/include' \
                       ' -I{p}/modules/zyre/include'.format(p=AIOZYRE_PATH)

        original_cppflags = os.environ.get('CPPFLAGS') or ''
        env['CPPFLAGS'] = extra_cflags + original_cppflags

        original_cflags = os.environ.get('CFLAGS') or ''
        env['CFLAGS'] = extra_cflags + original_cflags

        extra_ld_flags = ' -L{p}/modules/libzmq/src/.libs' \
                         ' -L{p}/modules/czmq/src/.libs' \
                         ' -L{p}/modules/zyre/src/.libs'.format(p=AIOZYRE_PATH)

        original_ldflags = os.environ.get('LDFLAGS') or ''
        env['LDFLAGS'] = extra_ld_flags + original_ldflags

        for cwd, cmds in LIBS:
            for cmd in cmds:
                print(cmd)
                #subprocess.check_call(cmd, cwd=cwd, env=env)
        print("HEYYYOOO")
        build_ext.run(self)


class Clean(clean):
    def run(self):
        for cwd, _ in LIBS:
            try:
                pass
                #subprocess.check_call(['make', 'clean'], cwd=cwd)
            except:
                pass
        clean.run(self)


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
            extra_objects=get_extra_objects(),
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
