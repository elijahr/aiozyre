import os

from setuptools import setup, Extension

try:
    from Cython.Build import cythonize
except ImportError:
    # Cython not available, build from C
    mod_ext = 'c'

    def cythonize(extensions, *args, **kwargs):
        return extensions
else:
    mod_ext = 'pyx'


def fullpath(path):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), path)


with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name='aiozyre',
    version='1.0.2',
    description='asyncio-friendly Python bindings for Zyre',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Elijah Shaw-Rutschman',
    author_email='elijahr+aiozyre@gmail.com',
    packages=['aiozyre'],
    ext_modules=cythonize([
        Extension('aiozyre.futures', sources=[fullpath('aiozyre/futures.%s' % mod_ext)]),
        Extension('aiozyre.node', sources=[fullpath('aiozyre/node.%s' % mod_ext)]),
        Extension('aiozyre.nodeactor', sources=[fullpath('aiozyre/nodeactor.%s' % mod_ext)], libraries=['czmq', 'zyre']),
        Extension('aiozyre.nodeconfig', sources=[fullpath('aiozyre/nodeconfig.%s' % mod_ext)]),
        Extension('aiozyre.signals', sources=[fullpath('aiozyre/signals.%s' % mod_ext)]),
        Extension('aiozyre.util', sources=[fullpath('aiozyre/util.%s' % mod_ext)], libraries=['czmq', 'zyre']),
        Extension('aiozyre.zyre', sources=[fullpath('aiozyre/zyre.%s' % mod_ext)], libraries=['czmq', 'zyre']),
    ]),
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
