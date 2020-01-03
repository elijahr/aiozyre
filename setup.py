
from setuptools import setup, Extension


with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name='aiozyre',
    version='1.0.4',
    description='asyncio-friendly Python bindings for Zyre',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Elijah Shaw-Rutschman',
    author_email='elijahr+aiozyre@gmail.com',
    packages=['aiozyre'],
    package_data={'': [
        'aiozyre/futures.pyx',
        'aiozyre/node.pyx',
        'aiozyre/nodeactor.pyx',
        'aiozyre/nodeconfig.pyx',
        'aiozyre/signals.pyx',
        'aiozyre/util.pyx',
        'aiozyre/zyre.pyx',
    ]},
    ext_modules=[
        Extension('aiozyre.futures', sources=['aiozyre/futures.pyx']),
        Extension('aiozyre.node', sources=['aiozyre/node.pyx']),
        Extension('aiozyre.nodeactor', sources=['aiozyre/nodeactor.pyx'], libraries=['czmq', 'zyre']),
        Extension('aiozyre.nodeconfig', sources=['aiozyre/nodeconfig.pyx']),
        Extension('aiozyre.signals', sources=['aiozyre/signals.pyx']),
        Extension('aiozyre.util', sources=['aiozyre/util.pyx'], libraries=['czmq', 'zyre']),
        Extension('aiozyre.zyre', sources=['aiozyre/zyre.pyx'], libraries=['czmq', 'zyre']),
    ],
    setup_requires=['cython'],
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
