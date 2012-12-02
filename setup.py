#!/usr/bin/env python
from setuptools import setup, find_packages

setup(name='django-pxpay',
      version='0.1',
      url='https://github.com/pavel-shpilev/django-pxpay',
      author="Pavel Shpilev",
      author_email="p.shpilev@gmail.com",
      description="PaymentExpress PxPay Gateway for Django",
      long_description=open('README.md').read(),
      keywords="PxPay, Payment, PaymentExpress, Django, Python",
      license='BSD',
      packages=find_packages(exclude=['sandbox*', 'tests*']),
      install_requires=['requests>=0.13.5'],
      include_package_data=True,
      # See http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=['Environment :: Web Environment',
                   'Framework :: Django',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python']
      )
