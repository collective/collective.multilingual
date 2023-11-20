#!/bin/sh
# Prerequisites: Python 3, virtualenv.
# Usage:
#     ./bootstrap.sh
python -m venv py
./py/bin/pip install -r https://dist.plone.org/release/5-latest/requirements.txt
./py/bin/buildout
