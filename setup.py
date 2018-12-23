from setuptools import setup, find_packages

setup(name='balance_check',
      version='0.1',
      description='Check gift card balances for a variety of providers',
      url='http://github.com/stevenmirabito/balance_check',
      author='Steven Mirabito',
      author_email='steven@stevenmirabito.com',
      license='MIT',
      packages=find_packages(),
      entry_points={
          'console_scripts': ['balance-check=balance_check.cli:main'],
      },
      install_requires=[
          'beautifulsoup4',
          'Cerberus',
          'colorlog',
          'luhn',
          'python3-anticaptcha',
          'requests',
          'tqdm'
      ])
