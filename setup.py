import pathlib

from setuptools import find_packages, setup

NAME = "kedro_mlflow"
HERE = pathlib.Path(__file__).parent


def _parse_requirements(path, encoding="utf-8"):
    with open(path, encoding=encoding) as file_handler:
        requirements = [
            x.strip() for x in file_handler if x.strip() and not x.startswith("-r")
        ]
    return requirements


# get the dependencies and installs
base_requirements = _parse_requirements("requirements.txt")


# Get the long description from the README file
with open((HERE / "README.md").as_posix(), encoding="utf-8") as file_handler:
    README = file_handler.read()


setup(
    name=NAME,
    version="0.13.2",  # this will be bumped automatically by bump-my-version
    description="A kedro-plugin to use mlflow in your kedro projects",
    license="Apache Software License (Apache 2.0)",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/Galileo-Galilei/kedro-mlflow",
    python_requires=">=3.8, <3.12",
    packages=find_packages(exclude=["docs*", "tests*"]),
    setup_requires=["setuptools_scm"],
    include_package_data=True,
    install_requires=base_requirements,
    extras_require={
        "doc": [
            "sphinx>=4.5.0,<8.0.0",
            "sphinx_rtd_theme>=1.0,<1.5",
            "sphinx-markdown-tables~=0.0.15",
            "sphinx-click>=3.1,<6.1",
            "sphinx_copybutton~=0.5.0",
            "myst-parser>=0.17.2,<4.1.0",
        ],
        "test": [
            "pytest>=5.4.0, <8.0.0",  # pytest==8.0.0 breaks pytest-lazy-fixture : https://github.com/TvoroG/pytest-lazy-fixture/issues/65
            "pytest-cov>=2.8.0, <6.0.0",
            "pytest-lazy-fixture>=0.6.0, <1.0.0",
            "pytest-mock>=3.1.0, <4.0.0",
            "ruff>=0.5.0,<0.6.0",  # ensure consistency with pre-commit
            "scikit-learn>=0.23.0, <1.6.0",
            "kedro-datasets[pandas.CSVDataSet]",
        ],
        "dev": [
            "pre-commit>=2.0.0,<4.0.0",
            "jupyter>=1.0.0,<2.0.0",
        ],
    },
    author="Yolan Honoré-Rougé",
    entry_points={
        "kedro.project_commands": [
            "kedro_mlflow =  kedro_mlflow.framework.cli.cli:commands"
        ],
        "kedro.hooks": [
            "mlflow_hook = kedro_mlflow.framework.hooks.mlflow_hook:mlflow_hook",
        ],
    },
    zip_safe=False,
    keywords="kedro-plugin, mlflow, model versioning, model packaging, pipelines, machine learning, data pipelines, data science, data engineering",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Framework :: Kedro",
        "Environment :: Plugins",
        "Intended Audience :: Developers",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
    ],
)
