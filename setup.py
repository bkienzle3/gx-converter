from setuptools import setup, find_packages

setup(
    name="gx_converter",
    version="0.2.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "gx-converter=gx_converter.main:main",
        ],
    },
    include_package_data=True,
    python_requires=">=3.9",
)
