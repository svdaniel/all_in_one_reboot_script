from setuptools import setup, find_packages
from codecs import open
from os import path

from reboot_script import release

here = path.abspath(path.dirname(__file__))

# get the dependencies and installs
with open(path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    all_reqs = f.read().split('\n')

install_requires = [x.strip() for x in all_reqs if 'git+' not in x]
dependency_links = [x.strip().replace('git+', '') for x in all_reqs if x.startswith('git+')]

setup(
    name='enhanced-reboot-script',
    version=release.__version__,
    description='reboot-script',
    long_description=release.__description__,
    url=release.__github__,
    download_url=release.__github__ + '/tarball/' + release.__version__,
    license='BSD',
    classifiers=[
      'Development Status :: 3 - Alpha',
      'Intended Audience :: Developers',
      'Programming Language :: Python :: 3',
    ],
    keywords='',
    packages=find_packages(exclude=['docs', 'tests*', 'venv', 'temp']),
    include_package_data=True,
    author=release.__author__,
    install_requires=install_requires,
    dependency_links=dependency_links,
    author_email=release.__author_email__
)
