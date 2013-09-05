import os
from setuptools import setup, find_packages
import glob

src_dir = os.path.dirname(__file__)

def read(filename):
    full_path = os.path.join(src_dir, filename)
    with open(full_path) as fd:
        return fd.read()


setup(
    name='nymms',
    version='0.2.1',
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
    scripts=glob.glob(os.path.join(src_dir, 'scripts', '*')),
)
