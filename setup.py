from setuptools import setup
 
setup(
    name='CreateCloudMap',
    version='0.1.0',
    packages=['cloudmap', ],
    license='LICENSE',
    description='Python script to create a cloud map for xplanet using satellite images from the Dundee Satellite Receiving Station, Dundee University, UK',
    long_description=open('README.md').read(),
    author='Joachim Herb',
    author_email='Joachim.Herb@gmx.de',
    install_requires=['pyresample', 'numpy', 'scipy', 'requests', 'datetime', 
                      'argparse', 'ConfigParser', 'PIL'],
    entry_points={
        'console_scripts': [
            'create_map = cloudmap.create_map:main',
        ]
    }
)