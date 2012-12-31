from distutils.core import setup
import os

longdesc = \
'''An API to read and analyze CSV files by inferring types for each column of
data.

Currently, only int, float and string types are supported.'''

try:
    docfiles = map(lambda s: 'doc/%s' % s, list(os.walk('doc'))[0][2])
except IndexError:
    docfiles = []

setup(
    name='qcsv',
    author='Andrew Gallant',
    author_email='qcsv@burntsushi.net',
    version='0.0.1',
    license='WTFPL',
    description='An API to read and analyze CSV files.',
    long_description=longdesc,
    url='https://github.com/BurntSushi/qcsv',
    classifiers=[
        'License :: Public Domain',
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Other Audience',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Database',
    ],
    platforms='ANY',
    packages=['qcsv'],
    package_dir={'qcsv': '.'},
    package_data={'qcsv': ['sample.csv']},
    data_files=[('share/doc/qcsv', ['README', 'COPYING', 'INSTALL']),
                ('share/doc/qcsv/doc', docfiles)],
    scripts=[]
)
