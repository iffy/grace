from distutils.core import setup

setup(
    url='https://github.com/iffy/grace',
    author='Matt Haggard',
    author_email='haggardii@gmail.com',
    name='grace',
    version='0.1',
    packages=[
        'grace', 'grace.test',
    ],
    install_requires=[
        'Twisted>=10.2.0',
    ],
    scripts=[
        'bin/grace',
    ]
)
