import pathlib
from setuptools import setup
from simba import info

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="simba",
    version=info.version,
    description="Manage output from scientific simulations",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/solidsuccs/simba",
    author="Brandon Runnels",
    author_email="brunnels@uccs.edu",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    packages=["simba"],
    include_package_data=True,
    install_requires=["Flask>=0.2","Frozen-Flask","Flask-Markdown","terminaltables","pysqlite3"],
    python_requires='>3.6',
    scripts=['bin/simba']
    #entry_points={
    #    "console_scripts": [
    #        "simba=simba.__main__:main",
    #    ]
    #},
)
