from setuptools import find_packages
from setuptools import setup

import os
import sys


long_description = "\n\n".join(
    [
        open("README.rst").read(),
        open("CHANGES.rst").read(),
    ]
)


setup(
    name="collective.multilingual",
    version="2.0",
    description="Create, relate and manage content in multiple languages in Plone!",
    long_description=long_description,
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: Addon",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords="plone multilingual dexterity",
    author="Malthe Borch",
    author_email="mborch@gmail.com",
    license="GPL version 2",
    packages=find_packages("src"),
    package_dir={"": "src"},
    namespace_packages=["collective"],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "setuptools",
        "plone.app.dexterity",
        "plone.behavior",
        "plone.formwidget.contenttree",
    ],
    extras_require={
        "test": [
            "plone.testing>=4.0.6",
            "plone.app.testing",
            "lxml",
        ]
    },
    entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
)
