from setuptools import setup

setup(
    name='bt_ccxtpro_store',
    version='0.1',
    description='A CCXT Pro Store Work with some additions',
    url='https://github.com/xiangxn/bt-ccxtpro-store',
    author='Necklace',
    author_email='xiangxn@163.com',
    license='MIT',
    packages=['ccxtpro'],
    install_requires=['backtrader@git+https://github.com/xiangxn/backtrader.git@async#egg=backtrader', 'ccxt'],
)
