from distutils.core import setup, Extension

module = Extension(
    "ImPasta",
    libraries=["ImPasta"],
    library_dirs=["build/Debug/"],
    sources=[]
)

setup(name="ImPasta", version="1.0", ext_modules=[module])
