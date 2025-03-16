#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("requirements.txt") as requirements_file:
    requirements = list(map(str.strip, requirements_file.read().splitlines()))

setup(
    author="purarue, 1337-server, lydiazly",
    name="pythonanywhere-3-months",
    description='A modified version of pythonanywhere-3-months (forked from 1337-server/pythonanywhere-3-months, which was forked from purarue/pythonanywhere-3-months).',
    python_requires='>=3.10',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    install_requires=requirements,
    license="Unlicense",
    include_package_data=True,
    packages=find_packages(include=["pythonanywhere_3_months"]),
    entry_points={
        "console_scripts": [
            "pythonanywhere_3_months = pythonanywhere_3_months.__main__:main",
            "pythonanywhere_check_since = pythonanywhere_3_months.last_run:check",
        ]
    },
    url="https://github.com/lydiazly/pythonanywhere-3-months",
    version="0.1.0",
    zip_safe=True,
)
