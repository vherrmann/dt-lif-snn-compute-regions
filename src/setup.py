from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import pybind11


class BuildExt(build_ext):
    """Custom build extension to set compiler flags."""

    def build_extensions(self):
        c = self.compiler.compiler_type
        opts = []
        if c == "unix":
            opts = ["-O3", "-fno-math-errno", "-fPIC", "-DNDEBUG"]
            for ext in self.extensions:
                ext.extra_compile_args = opts
        build_ext.build_extensions(self)


print([pybind11.get_include()])
ext_modules = [
    Extension(
        "unique_bytes",
        ["unique_bytes.cpp"],
        include_dirs=[pybind11.get_include()],
        language="c++",
    )
]

setup(
    name="unique_bytes",
    version="0.1",
    ext_modules=ext_modules,
    cmdclass={"build_ext": BuildExt},
)

# build with
# python setup.py build_ext --inplace
