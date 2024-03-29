import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.txt')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.txt')) as f:
    CHANGES = f.read()

requires = [
    'pyramid',
    'pyramid_debugtoolbar',
    'pyramid_tm',
    'SQLAlchemy',
    'transaction',
    'zope.sqlalchemy',
    'waitress',
    'inflection',
    'formencode',
    'alembic',
    'decorator'
    ]

setup(name='WebRPG',
      version='0.6.0',
      description='WebRPG',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Programming Language :: Python :: 3 :: Only",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web wsgi bfg pylons pyramid',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      include_package_data=True,
      zip_safe=False,
      test_suite='webrpg',
      install_requires=requires,
      entry_points="""\
      [paste.app_factory]
      main = webrpg:main
      [console_scripts]
      WebRPG = webrpg.scripts.main:main
      """,
      )
