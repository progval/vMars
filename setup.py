from distutils.core import setup
from distutils.extension import Extension

try:
    from Cython.Distutils import build_ext
    cmdclass = {'build_ext': build_ext}
    ext_modules = [Extension("vmars.core", ["lib/core.py"])]
except ImportError:
    cmdclass = {}
    ext_modules = []

setup(
    name = 'vmars',
    cmdclass = cmdclass,
    ext_modules = ext_modules,
    packages = ['vmars'],
    package_dir = {'vmars': 'lib'},
    scripts=['bin/vcore',
            'bin/vasm',
            ]
    )
