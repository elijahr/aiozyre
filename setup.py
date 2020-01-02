
from setuptools import setup, Extension

try:
    from Cython.Build import cythonize
except ImportError:
    def cythonize(*args, **kwargs):
        from Cython.Build import cythonize
        return cythonize(*args, **kwargs)

with open("README.md", "r") as fh:
    long_description = fh.read()

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
    ext_modules=cythonize([
        Extension('aiozyre.futures', sources=['aiozyre/futures.pyx']),
        Extension('aiozyre.node', sources=['aiozyre/node.pyx']),
        Extension('aiozyre.nodeactor', sources=['aiozyre/nodeactor.pyx']),
        Extension('aiozyre.nodeconfig', sources=['aiozyre/nodeconfig.pyx']),
        Extension('aiozyre.signals', sources=['aiozyre/signals.pyx']),
        Extension('aiozyre.util', sources=['aiozyre/util.pyx']),
        Extension('aiozyre.zyre', sources=['aiozyre/zyre.pyx'], libraries=['czmq', 'zyre']),
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
