
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
    install_requires=['cython'],
    setup_requires=['cython'],
    ext_modules=cythonize([
        Extension('aiozyre.futures', sources=['aiozyre/futures.%s' % mod_ext]),
        Extension('aiozyre.node', sources=['aiozyre/node.%s' % mod_ext]),
        Extension('aiozyre.nodeactor', sources=['aiozyre/nodeactor.%s' % mod_ext], libraries=['czmq', 'zyre']),
        Extension('aiozyre.nodeconfig', sources=['aiozyre/nodeconfig.%s' % mod_ext]),
        Extension('aiozyre.signals', sources=['aiozyre/signals.%s' % mod_ext]),
        Extension('aiozyre.util', sources=['aiozyre/util.%s' % mod_ext], libraries=['czmq', 'zyre']),
        Extension('aiozyre.zyre', sources=['aiozyre/zyre.%s' % mod_ext], libraries=['czmq', 'zyre']),
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
