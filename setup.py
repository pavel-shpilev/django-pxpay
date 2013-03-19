#!/usr/bin/env python
import os
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='django-pxpay',
    version='0.2.2',
    url='http://github.com/pavel-shpilev/django-pxpay',
    author="Pavel Shpilev",
    author_email="p.shpilev@gmail.com",
    description="PaymentExpress PxPay Gateway for Django",
    long_description=read('README.rst'),
    keywords="PxPay, Payment, PaymentExpress, DPS, Django, Python",
    license='BSD',
    packages=find_packages(exclude=['test']),
    install_requires=['requests>=0.13.5', 'django>=1.4'],
    include_package_data=True,
    classifiers=['Environment :: Web Environment',
                 'Framework :: Django',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: BSD License',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python'])
