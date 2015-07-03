
from setuptools import setup, find_packages

requires = [
    'buildbot',
    'python-debian',
    'xunitparser',
]

setup(
    name='buildbot-junit',
    version='0.1',
    description='Junit for buildbot',
    author='Andrey Stolbuhin',
    author_email='an.stol99@gmail.com',
    url='https://github.com/ZeeeL/buildbot-junit',
    keywords='buildbot xunit junit steps shellcommand',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
)
