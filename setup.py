#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2024/4/19 9:59
# @Author  : harilou
# @Describe:
from setuptools import setup, find_packages

setup(
    name='ops_sdk',
    version='0.0.0',
    install_requires=[
        'requests>=2.28.2',  # 你的项目依赖的库
        'PyYAML>=5.4.1',
    ],
    # 项目的元数据
    author='louwenjun',
    author_email='1084430062@qq.com',
    description='运维内部通用SDK',
    url='https://git-intra.123u.com/sa/ops_sdk',
    keywords='ops_sdk',
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console :: Curses',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9'
    ],
)
