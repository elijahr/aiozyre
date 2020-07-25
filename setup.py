import glob
import itertools
import os
import sys

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext as _build_ext
from setuptools.command.install import install as _install


DIR = os.path.dirname(__file__)


with open("README.md", "r") as fh:
    long_description = fh.read()


class build_ext(_build_ext):
    def initialize_options(self):
        super(build_ext, self).initialize_options()
        self.debug = '--debug' in sys.argv

    def finalize_options(self):
        from Cython.Build.Dependencies import cythonize
        for item in itertools.chain(
                glob.glob(os.path.join(DIR, 'src', 'aiozyre', '*.c')),
                glob.glob(os.path.join(DIR, 'src', 'aiozyre', '*.h'))):
            os.remove(item)

        self.distribution.ext_modules[:] = cythonize(
            self.distribution.ext_modules,
            gdb_debug=self.debug,
        )

        super(build_ext, self).finalize_options()

        # Never install as an egg
        self.single_version_externally_managed = False


class install(_install):
    user_options = _install.user_options + [
        ('debug', None, 'Build with debug symbols'),
    ]

    def initialize_options(self):
        super(install, self).initialize_options()
        self.debug = '--debug' in sys.argv

    def finalize_options(self):
        super(install, self).finalize_options()
        # Never install as an egg
        self.single_version_externally_managed = False


def get_pyx():
    for path in glob.glob(os.path.join(DIR, 'src', 'aiozyre', '*.pyx')):
        module = 'aiozyre.%s' % os.path.splitext(os.path.basename(path))[0]
        source = os.path.join('src', 'aiozyre', os.path.basename(path))
        yield module, source


setup(
    name='aiozyre',
    version='1.1.5',
    description='asyncio-friendly Python bindings for Zyre',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Elijah Shaw-Rutschman',
    author_email='elijahr+aiozyre@gmail.com',
    packages=['aiozyre'],
    package_dir={
      'aiozyre': os.path.join('src', 'aiozyre'),
    },
    data_files=['README.md', 'LICENSE'],
    package_data={
        'aiozyre': [
            # Include cython source
            '*.pyx',
            '*.pxd',
        ],
    },
    cmdclass={
        'build_ext': build_ext,
        'install': install
    },
    ext_modules=[
        Extension(
            module,
            sources=[source],
            libraries=['czmq', 'zyre'],
        )
        for module, source in get_pyx()
    ],
    setup_requires=['cython'],
    extras_require={
        'dev': [
            'blessed',
            'aioconsole',
        ]
    },
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3',
        'Topic :: System :: Networking',
        'Framework :: AsyncIO',
    ],
    zip_safe=False,
)
