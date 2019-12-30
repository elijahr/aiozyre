import subprocess

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext

try:
    from Cython.Build import cythonize
except ImportError:
    def cythonize(*args, **kwargs):
        from Cython.Build import cythonize
        return cythonize(*args, **kwargs)


# class BuildExt(build_ext):
#     def run(self):
#         subprocess.check_call(['make', 'clean'], cwd='pipe')
#         subprocess.check_call(['make', 'pipe_release'], cwd='pipe')
#         build_ext.run(self)


setup(
    name='aiozyre',
    version='0.1.0',
    description='asyncio-friendly Python bindings for Zyre',
    author='Elijah Shaw-Rutschman',
    author_email='elijahr+aiozyre@gmail.com',
    packages=['aiozyre'],
    setup_requires=[
        'cython',
    ],
    ext_modules=cythonize([
        Extension('aiozyre.actor', sources=['aiozyre/actor.pyx'], libraries=['czmq', 'zyre']),
        Extension('aiozyre.futures', sources=['aiozyre/futures.pyx'], libraries=['czmq', 'zyre']),
        Extension('aiozyre.node', sources=['aiozyre/node.pyx'], libraries=['czmq', 'zyre']),
        Extension('aiozyre.signals', sources=['aiozyre/signals.pyx'], libraries=['czmq', 'zyre']),
        Extension('aiozyre.util', sources=['aiozyre/util.pyx'], libraries=['czmq', 'zyre']),
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
