from setuptools import setup, find_packages

requires = [
    'dicompylercore',
    'fuzzywuzzy',
    'python-Levinshtein',
    'bokeh',
    'pydicom'
]

setup(
    name='dvh-check',
    include_package_data=True,
    packages=find_packages(),
    version=0.1,
    description='Check DVHs from DICOM against protocol constraints',
    author='Dan Cutright',
    author_email='dan.cutright@gmail.com',
    url='https://github.com/cutright/DVH-Check',
    download_url='https://github.com/cutright/DVH-Check/archive/master.zip',
    license="MIT License",
    keywords=['dvh', 'radiation therapy', 'dicom', 'dicom-rt', 'bokeh'],
    classifiers=[],
    install_requires=requires,
    entry_points={
        'console_scripts': [
            'dvh-check=dvh-check.__main__:main',
        ],
    },
    long_description="""DVH Checks
    Read RT DICOM files, evaluate protocol constraints using dicompyler, bokeh, and fuzzywuzzy.
    """
)