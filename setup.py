from setuptools import setup

setup(
    name='versionix',
    version='0.1.0',
    entry_points={
        'console_scripts': [
            'vsx=versionix.cli:main',
        ],
    },
    author='Enock Kipsang',
    author_email='kipsang.dev@gmail.com',
    description='A lightweight distributed version control system',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
)
