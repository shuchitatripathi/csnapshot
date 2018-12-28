from setuptools import setup

setup(
    name='snapagain',
    version='0.1',
    author='Shuchita',
    packages=['shotty'],
    description='Something',
    install_requires=[
        'click',
        'boto3'
    ],
    entry_points='''
        [console_scripts]
        shotty=shotty.shotty:cli
    ''',

)
