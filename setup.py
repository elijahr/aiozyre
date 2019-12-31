
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
        Extension('aiozyre.actor', sources=['aiozyre/actor.pyx'], libraries=['czmq', 'zyre'], extra_compile_args=['-g', '-O0']),
        Extension('aiozyre.futures', sources=['aiozyre/futures.pyx'], extra_compile_args=['-g', '-O0']),
        Extension('aiozyre.node', sources=['aiozyre/node.pyx'], libraries=['czmq', 'zyre'], extra_compile_args=['-g', '-O0']),
        Extension('aiozyre.nodeconfig', sources=['aiozyre/nodeconfig.pyx'], libraries=['czmq', 'zyre'], extra_compile_args=['-g', '-O0']),
        Extension('aiozyre.signals', sources=['aiozyre/signals.pyx'], extra_compile_args=['-g', '-O0']),
        Extension('aiozyre.util', sources=['aiozyre/util.pyx'], libraries=['czmq', 'zyre'], extra_compile_args=['-g', '-O0']),
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
