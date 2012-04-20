from setuptools import setup,find_packages

config = {
  'description':'git deployment tools',
  'version':'0.0.1',
  'name':'deployer',
  'package_dir': {'':'lib'},
  'packages': ['plop'],
  'entry_points': {
    'console_scripts':[
       'prereceiver=plop.prereceiver:main',
       'gitversion=plop.gitversion:main'
    ]
  }
}

setup(**config)
