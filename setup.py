import os
from setuptools import setup, find_packages
import glob

src_dir = os.path.dirname(__file__)

install_requires = [
    "arrow>=0.5.4",
    "boto>=2.36.0",
    "Flask>=0.10.1",
    "Jinja2>=2.7.3",
    "MarkupSafe>=0.23",
    "python-dateutil>=2.4.0",
    "PyYAML>=3.11",
    "schematics>=1.0.2",
    "six>=1.9.0",
    "validictory>=1.0.0",
    "Werkzeug>=0.10.1",
    "Flask-API==0.6.2",
]

tests_require = [
    'nose>=1.0',
]


def read(filename):
    full_path = os.path.join(src_dir, filename)
    with open(full_path) as fd:
        return fd.read()


if __name__ == '__main__':
    setup(
        name='nymms',
        version='0.5.0',
        author='Michael Barrett',
        author_email='loki77@gmail.com',
        license="New BSD license",
        url="https://github.com/cloudtools/nymms",
        description='Not Your Mother\'s Monitoring System (NYMMS)',
        long_description=read('README.rst'),
        classifiers=[
            "Topic :: System :: Monitoring",
            "License :: OSI Approved :: BSD License",
            "Development Status :: 3 - Alpha"],
        packages=find_packages(),
        scripts=glob.glob(os.path.join(src_dir, 'scripts', 'nymms_*')),
        install_requires=install_requires,
        tests_require=tests_require,
        test_suite='nose.collector',
    )
