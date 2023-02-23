#!/bin/bash

rm -rf dist/*
python -m build
python -m twine upload -r nodepasta dist/*