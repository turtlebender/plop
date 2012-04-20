from setuptools import setup,find_packages

config = {
  'description':'git deployment tools',
  'version':'0.0.1',
  'name':'deployer',
  'package_dir': {'':'lib'},
  'packages': ['deployer'],
  'entry_points': {
    'console_scripts':[
       'prereceiver=deployer.prereceiver:main',
       'gitversion=deployer.gitversion:main'
    ]
  }
}

setup(**config)
