# setup.py

from setuptools import setup, find_packages

setup(
    name='Tudo',
    version='0.1',
    description="Taxonomy of utterances and dynamic oscillations",
    author='Sem Ribeiro Albuquerque Wendt',
    author_email='sem@16161d.net',
    url='https://gitea.com/sem-16161d/Tudo',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'numpy', 'librosa', 'scipy', 
        'GreasyPidgin', 'psycopg2'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    
)