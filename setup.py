import re
import pathlib
from setuptools import find_packages, setup

NAME = "kedro_mlflow"
HERE = pathlib.Path(__file__).parent

# get package version
with open((HERE / NAME / "__init__.py").as_posix(), encoding="utf-8") as file_handler:
    result = re.search(r'__version__ *= *["\']([^"\']+)', file_handler.read())

    if not result:
        raise ValueError("Can't find the version in kedro/__init__.py")

    VERSION = result.group(1)

def _get_requirements(path, encoding="utf-8"):
    with open(path, mode="r", encoding=encoding) as file_handler:
        requirements = [x.strip() for x in file_handler if x.strip() and not x.startswith("-r")]
    return requirements

# get the dependencies and installs
base_requirements= _get_requirements("requirements/requirements.txt")
test_requirements= _get_requirements("requirements/test_requirements.txt")


# Get the long description from the README file
with open((HERE / "README.md").as_posix(), encoding="utf-8") as file_handler:
    README = file_handler.read()


setup(
    name=NAME,
    version=VERSION,
    description="A kedro-plugin to use mlflow in your kedro projects",
    license="Apache Software License (Apache 2.0)",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/Galileo-Galilei/kedro-mlflow",
    python_requires=">=3.6, <3.9",
    packages=find_packages(exclude=["docs*", "tests*"]),
    include_package_data=True,
    tests_require=test_requirements,
    install_requires=base_requirements,
    author="Galileo-Galilei",
    entry_points={
        "kedro.project_commands": ["kedro_mlflow =  kedro_mlflow.cli.cli:commands"],
        "kedro.global_commands": ["kedro_mlflow =  kedro_mlflow.cli.cli:commands"]
        },
    zip_safe=False,
    keywords="kedro plugin, mlflow, model versioning, model packaging, pipelines, machine learning, data pipelines, data science, data engineering",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)