import os
import sys

reload(sys).setdefaultencoding("UTF-8")

from setuptools import setup, find_packages


def read(*pathnames):
    try:
        return open(os.path.join(os.path.dirname(__file__), *pathnames)).read().\
            decode('utf-8')
    except:
        # Doesn't work under tox/pip
        return u""

version = '1.0.1'

setup(name='collective.multilingual',
      version=version,
      description="Create, relate and manage content in multiple languages in Plone!",
      long_description='\n'.join([
          read('README.rst'),
          read('CHANGES.rst'),
          ]),
      classifiers=[
        "Framework :: Plone",
        "Framework :: Zope2",
        "Programming Language :: Python",
        ],
      keywords='plone multilingual dexterity',
      author='Malthe Borch',
      author_email='mborch@gmail.com',
      license="GPLv2+",
      packages=find_packages('src'),
      package_dir={'': 'src'},
      namespace_packages=['collective'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'Products.CMFPlone>=4.1',
          'plone.app.dexterity',
          'plone.behavior',
      ],
      extras_require = {
          'test': [
              'plone.testing>=4.0.6',
              'plone.app.testing',
              'lxml',
              ]
          },
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
