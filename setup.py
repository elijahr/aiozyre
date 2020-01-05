
from setuptools import setup, Extension


with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name='aiozyre',
    version='1.1.2',
    description='asyncio-friendly Python bindings for Zyre',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Elijah Shaw-Rutschman',
    author_email='elijahr+aiozyre@gmail.com',
    packages=['aiozyre'],
    package_dir={
      'aiozyre': 'src/aiozyre',
    },
    package_data={'aiozyre': [
        '*.pyx',
        '*.pxd',
    ]},
    ext_modules=[
        Extension('aiozyre.nodeactor', sources=['src/aiozyre/nodeactor.pyx'], libraries=['czmq', 'zyre']),
        Extension('aiozyre.signals', sources=['src/aiozyre/signals.pyx']),
        Extension('aiozyre.util', sources=['src/aiozyre/util.pyx'], libraries=['czmq', 'zyre']),
    ],
    setup_requires=['cython'],
    extras_require={
        'dev': [
            'blessed',
            'aioconsole',
        ]
    },
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
