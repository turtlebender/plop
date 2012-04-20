from setuptools import setup

CONFIG = {
  'description':'git deployment tools',
  'version':'0.0.1',
  'name':'plop',
  'package_dir': {'':'lib'},
  'packages': ['plop'],
  'entry_points': {
    'console_scripts':[
       'prereceiver=plop.prereceiver:main',
       'gitversion=plop.gitversion:main',
       'plop-server=plop.server:main',
       'elbhelper=plop.ec2:main'
    ]
  }
}

setup(**CONFIG)
