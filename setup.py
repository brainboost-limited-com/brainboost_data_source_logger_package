from setuptools import setup, find_packages

setup(
    name='brainboost_data_source_logger_package',
    version='1.0.0',
    author='Pablo Tomas Borda',
    author_email='pablotomasborda@gmail.com',
    description='A package for logging data sources in BrainBoost projects.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/brainboost_data_source_logger_package',
    packages=find_packages(),
    install_requires=[
        'requests>=2.25.1',
        'brainboost_configuration_package'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
