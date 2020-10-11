**General informations**

[![Python Version](https://img.shields.io/badge/python-3.6%20%7C%203.7%20%7C%203.8-blue.svg)](https://pypi.org/project/kedro-mlflow/) [![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0) [![Code Style: Black](https://img.shields.io/badge/code%20style-black-black.svg)](https://github.com/ambv/black)

----------------------------------------------------------
| Software repository | Latest release | Total downloads |
|---------------------|----------------|-----------------|
| Pypi | [![PyPI version](https://badge.fury.io/py/kedro-mlflow.svg)](https://pypi.org/project/kedro-mlflow/) | [![Downloads](https://pepy.tech/badge/kedro-mlflow)](https://pepy.tech/project/kedro-mlflow) |

**Code health**

----------------------------------------------------------
| Branch | Tests | Coverage | Documentation | Deployment |
|--------|-------|----------|---------------|------------|
| `develop`| [![test](https://github.com/Galileo-Galilei/kedro-mlflow/workflows/test/badge.svg?branch=develop)](https://github.com/Galileo-Galilei/kedro-mlflow/actions?query=workflow%3Atest+branch%3Adevelop)| [![codecov](https://codecov.io/gh/Galileo-Galilei/kedro-mlflow/branch/develop/graph/badge.svg)](https://codecov.io/gh/Galileo-Galilei/kedro-mlflow/branch/develop)|[![Documentation](https://readthedocs.org/projects/kedro-mlflow/badge/?version=latest)](https://kedro-mlflow.readthedocs.io/en/latest/)| [![create-release-candidate](https://github.com/Galileo-Galilei/kedro-mlflow/workflows/create-release-candidate/badge.svg?branch=develop)](https://github.com/Galileo-Galilei/kedro-mlflow/actions?query=branch%3Adevelop+workflow%3Acreate-release-candidate)|
| `master` | [![test](https://github.com/Galileo-Galilei/kedro-mlflow/workflows/test/badge.svg?branch=master)](https://github.com/Galileo-Galilei/kedro-mlflow/actions?query=workflow%3Atest+branch%3Amaster) | [![codecov](https://codecov.io/gh/Galileo-Galilei/kedro-mlflow/branch/master/graph/badge.svg)](https://codecov.io/gh/Galileo-Galilei/kedro-mlflow/branch/master)|[![Documentation](https://readthedocs.org/projects/kedro-mlflow/badge/?version=stable)](https://kedro-mlflow.readthedocs.io/en/stable/)|[![publish](https://github.com/Galileo-Galilei/kedro-mlflow/workflows/publish/badge.svg?branch=master)](https://github.com/Galileo-Galilei/kedro-mlflow/actions?query=branch%3Amaster+workflow%3Apublish)|

**Main contributors**

The following people actively maintain, enhance and discuss design to make this package as good as possible. Many thanks to them!
- [Yolan Honoré-Rougé](https://github.com/galileo-galilei)
- [Kajetan Maurycy Olszewski](https://github.com/kaemo)
- [Adrian Piotr Kruszewski](https://github.com/akruszewski)
- [Takieddine Kadiri](https://github.com/takikadiri)


# Release and roadmap
The [release history](https://github.com/Galileo-Galilei/kedro-mlflow/blob/develop/CHANGELOG.md) centralizes packages improvements across time. The main features coming in next releases are [listed on github milestones](https://github.com/Galileo-Galilei/kedro-mlflow/milestones). Feel free to upvote/downvote and discuss prioritization in associated issues.

# What is kedro-mlflow?
``kedro-mlflow`` is a [kedro-plugin](https://kedro.readthedocs.io/en/stable/04_user_guide/10_developing_plugins.html) for lightweight and portable integration of [mlflow](https://mlflow.org/docs/latest/index.html) capabilities inside [kedro](https://kedro.readthedocs.io/en/stable/index.html) projects. It enforces [``Kedro`` principles]() to make mlflow usage as production ready as possible. Its core functionalities are :
- **versioning**: you can effortlessly register your parameters or your datasets with minimal configuration in a kedro run. Later, you will be able to browse your runs in the mlflow UI, and retrieve the runs you want. This is directly linked to [Mlflow Tracking](https://www.mlflow.org/docs/latest/tracking.html).
- **model packaging**: ``kedro-mlflow`` offers a convenient API to register a pipeline as a ``model`` in the mlflow sense. Consequently, you can *API-fy* or serve your kedro pipeline with one line of code, or share a model with without worrying of the preprocessing to be made for further use. This is directly linked to [Mlflow Models](https://www.mlflow.org/docs/latest/models.html).


# How do I install kedro-mlflow?
**Important: kedro-mlflow is only compatible with ``kedro>0.16.0``. If you have a project created with an older version of ``Kedro``, see this [migration guide](https://github.com/quantumblacklabs/kedro/blob/master/RELEASE.md#migration-guide-from-kedro-015-to-016).**

``kedro-mlflow`` is available on PyPI, so you can install it with ``pip``:
```console
pip install kedro-mlflow
```
If you want to use the ``develop`` version of the package which is the most up to date, you can install the package from github:
```console
pip install --upgrade git+https://github.com/Galileo-Galilei/kedro-mlflow.git@develop
```

I strongly recommend to use ``conda`` (a package manager) to create an environment and to read [``kedro`` installation guide](https://kedro.readthedocs.io/en/stable/02_getting_started/01_prerequisites.html).



# Getting started:
The documentation contains:
- [A "hello world" example](https://kedro-mlflow.readthedocs.io/en/latest/source/02_hello_world_example/index.html) which demonstrates how you to **setup your project**, **version parameters** and **datasets**, and browse your runs in the UI.
- A more [detailed tutorial](https://kedro-mlflow.readthedocs.io/en/latest/source/03_tutorial/index.html) to show more advanced features (mlflow configuration through the plugin, package and serve a kedro ``Pipeline``...)

Some frequently asked questions on more advanced features:
- You want to log additional metrics to the run? -> [Try ``MlflowMetricsDataSet``](https://kedro-mlflow.readthedocs.io/en/latest/source/03_tutorial/07_version_metrics.html) !
- You want to log nice dataviz of your pipeline that you register with ``MatplotlibWriter``? -> [Try ``MlflowArtifactDataSet`` to log any local files (.png, .pkl, .csv...) *automagically*](https://kedro-mlflow.readthedocs.io/en/latest/source/02_hello_world_example/02_first_steps.html#artifacts)!
- You want to create easily an API to share your awesome model to anyone? -> [See if ``pipeline_ml_factory`` can fit your needs](https://github.com/Galileo-Galilei/kedro-mlflow/issues/16)
- You want to do something that is not straigthforward with current implementation? Open an issue, and let's see what happens!

# Can I contribute?

I'd be happy to receive help to maintain and improve the package. Please check the [contributing guidelines](https://github.com/Galileo-Galilei/kedro-mlflow/blob/develop/CONTRIBUTING.md).
