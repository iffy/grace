from distutils.core import setup

#------------------------------------------------------------------------------
# from http://goo.gl/5sLpv
# for installing twisted plugins
#------------------------------------------------------------------------------
try:
    from setuptools.command import egg_info
    egg_info.write_toplevel_names
except (ImportError, AttributeError):
    pass
else:
    def _top_level_package(name):
        return name.split('.', 1)[0]

    def _hacked_write_toplevel_names(cmd, basename, filename):
        pkgs = dict.fromkeys(
            [_top_level_package(k)
                for k in cmd.distribution.iter_distribution_names()
                if _top_level_package(k) != "twisted"
            ]
        )
        cmd.write_file("top-level names", filename, '\n'.join(pkgs) + '\n')

    egg_info.write_toplevel_names = _hacked_write_toplevel_names
#------------------------------------------------------------------------------


setup(
    url='https://github.com/iffy/grace',
    author='Matt Haggard',
    author_email='haggardii@gmail.com',
    name='grace',
    version='0.1',
    packages=[
        'grace', 'grace.test',
        'twisted.plugins',
    ],
    install_requires=[
        'Twisted>=10.2.0',
    ],
    scripts=[
        'bin/grace',
    ]
)


#------------------------------------------------------------------------------
# also from http://goo.gl/5sLpv
#------------------------------------------------------------------------------
# Make Twisted regenerate the dropin.cache, if possible.  This is necessary
# because in a site-wide install, dropin.cache cannot be rewritten by
# normal users.
try:
    from twisted.plugin import IPlugin, getPlugins
except ImportError:
    pass
else:
    list(getPlugins(IPlugin))

