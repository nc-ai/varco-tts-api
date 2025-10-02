import os
import re

from setuptools import setup
from setuptools import find_packages
from setuptools.command.install import install as _install
from setuptools.command.develop import develop as _develop
from setuptools.command.egg_info import egg_info as _egg_info


here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with open(os.path.join(here, *parts), 'r') as f:
        return f.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r'__version__ = [\'\"]([^\'\"]*)[\'\"]', version_file)

    if version_match:
        version = version_match.group(1)
        return version
    else:
        raise RuntimeError('Unable to find version string')


class _cmd_dist:
    class develop(_develop):
        def run(self):
            print("setup with develop")
            # _exec_install_mecab()
            _develop.run(self)

    class install(_install):
        def initialize_options(self) -> None:
            super().initialize_options()

        def finalize_options(self) -> None:
            super().finalize_options()

        def run(self):
            _install.run(self)

    class egg_info(_egg_info):
        def initialize_options(self) -> None:
            super().initialize_options()

        def finalize_options(self) -> None:
            super().finalize_options()

        def run(self):
            _egg_info.run(self)

    def __init__(self):
        self.cmd_dict = {
            "develop" : self.develop,
            "install" : self.install,
            "egg_info": self.egg_info
        }

    def __call__(self, cmd):
        return self.cmd_dict[cmd]


cmdcls_dist = _cmd_dist()

test_deps = [
    'pytest',
    'pytest-cov',
    'pytest-pycodestyle'
]


setup(
    name='nctp',
    version=find_version('nctp', '__init__.py'),
    description='NCTP is a Text Processor for NCTTS.',
    author='NCAI Voice AI Service',
    packages=find_packages(include=[
        'nctp',
        'nctp.dictionary',
        'nctp.ncg2pk',
        'nctp.ncg2pe',
        'nctp.ncg2pj',
        'nctp.ncg2pc',
        'nctp.ncg2pt',
        'nctp.ssml',
        'nctp.ssml.text_norm',
        'nctp.ssml.text_norm.converters',
        'nctp_e2k',
    ]),
    package_data={"nctp" : ["dictionary/dict_json/*.json*" ],
                  "nctp.ssml" : ["config-nc-ssml.json"]
                  },
    keywords='text processor',
    license='proprietary and confidential',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3.10',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    python_requires='>=3.10',
    tests_require=test_deps,
    install_requires=[
        'json5',
        'g2p_en',
        'jamo==0.4.1',
        'unidecode==1.1.1',
        'inflect==4.1.0',
        'gruut',
        'pypinyin',
        'pyopenjtalk',
        'transformers==4.36.2',
        'WeTextProcessing==0.1.11',
        'jieba',
        'pybind11==2.11.1',
        'fasttext==0.9.2',
        'dohq-artifactory==0.10.0',
        'pypinyin_g2pw==0.4.0',
        "singleton-decorator==1.0.0",
        "pykakasi==2.2.1",
        "kanjize==1.5.0",
        "beautifulsoup4"
    ],
    extras_require={
        'test': test_deps,
    },
    cmdclass={
        'develop': cmdcls_dist('develop'),
        'install': cmdcls_dist('install'),
        'egg_info' : cmdcls_dist('egg_info')
    }
)
