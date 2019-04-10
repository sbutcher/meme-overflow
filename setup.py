import os
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="memeoverflow (fork)",
    version="0.3.1",
    author="Ben Nuttall, modified for mastodon by sbutcher",
    description="Take questions posted on a particular Stack Exchange site, generate a meme out of it and toot it",
    license="OSI Approved :: BSD License",
    keywords=[
        'stackexchange',
        'stackoverflow',
        'meme',
        'twitter',
    ],
    url="https://github.com/sbutcher/meme-overflow",
    packages=find_packages(),
    requires=[
        'requests',
        'twython',
    ],
    long_description=read('description.rst'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Games/Entertainment",
    ]
)
