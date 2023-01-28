**General informations**
<!-- markdown-link-check-disable -->
[![Python Version](https://img.shields.io/pypi/pyversions/kedro-mlflow)](https://pypi.org/project/kedro-mlflow/) [![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0) [![Code Style: Black](https://img.shields.io/badge/code%20style-black-black.svg)](https://github.com/ambv/black)
[![SemVer](https://img.shields.io/badge/semver-2.0.0-green)](https://semver.org/)
<!-- markdown-link-check-enable -->

----------------------------------------------------------
| Package manager | Software repository | Latest release                                                                                                                                | Total downloads                                                                                                                 |
| --------------- | ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| ``pip``         | PyPI                | [![PyPI version](https://badge.fury.io/py/kedro-mlflow.svg)](https://pypi.org/project/kedro-mlflow/)                                          | [![Downloads](https://pepy.tech/badge/kedro-mlflow)](https://pepy.tech/project/kedro-mlflow)                                    |
| ``conda``       | conda-forge         | [![conda version](https://img.shields.io/conda/vn/conda-forge/kedro-mlflow?color=bright%20green)](https://anaconda.org/search?q=kedro+mlflow) | [![Downloads](https://img.shields.io/conda/dn/conda-forge/kedro-mlflow?color=blue)](https://anaconda.org/search?q=kedro+mlflow) |

**Code health**

----------------------------------------------------------
| Branch   | Tests                                                                                                                                                                                            | Coverage                                                                                                                                                         | Links                                                                                                                                                                                                           | Documentation                                                                                                                           | Deployment                                                                                                                                                                                                | Activity                                                                                                                                                              |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `master` | [![test](https://github.com/Galileo-Galilei/kedro-mlflow/workflows/test/badge.svg?branch=master)](https://github.com/Galileo-Galilei/kedro-mlflow/actions?query=workflow%3Atest+branch%3Amaster) | [![codecov](https://codecov.io/gh/Galileo-Galilei/kedro-mlflow/branch/master/graph/badge.svg)](https://codecov.io/gh/Galileo-Galilei/kedro-mlflow/branch/master) | [![links](https://github.com/Galileo-Galilei/kedro-mlflow/workflows/check-links/badge.svg?branch=master)](https://github.com/Galileo-Galilei/kedro-mlflow/actions?query=workflow%3Acheck-links+branch%3Amaster) | [![Documentation](https://readthedocs.org/projects/kedro-mlflow/badge/?version=stable)](https://kedro-mlflow.readthedocs.io/en/stable/) | [![publish](https://github.com/Galileo-Galilei/kedro-mlflow/workflows/publish/badge.svg?branch=master)](https://github.com/Galileo-Galilei/kedro-mlflow/actions?query=branch%3Amaster+workflow%3Apublish) | [![commit](https://img.shields.io/github/commits-since/Galileo-Galilei/kedro-mlflow/0.11.7)](https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.11.7...master) |

*If you like the repo, please give it a :star:*

# What is kedro-mlflow?

``kedro-mlflow`` is a [kedro-plugin](https://kedro.readthedocs.io/en/stable/extend_kedro/plugins.html) for lightweight and portable integration of [mlflow](https://mlflow.org/docs/latest/index.html) capabilities inside [kedro](https://kedro.readthedocs.io/en/stable/index.html) projects. It enforces [``Kedro`` principles](https://kedro.readthedocs.io/en/stable/12_faq/01_faq.html?highlight=principles#what-is-the-philosophy-behind-kedro) to make mlflow usage as production ready as possible. Its core functionalities are :

- **versioning**: `kedro-mlflow` intends to enhance reproducibility for machine learning experimentation. With `kedro-mlflow` installed, you can effortlessly register your parameters or your datasets with minimal configuration in a kedro run. Later, you will be able to browse your runs in the mlflow UI, and retrieve the runs you want. This is directly linked to [Mlflow Tracking](https://www.mlflow.org/docs/latest/tracking.html).
- **model packaging**: ``kedro-mlflow`` intends to be be an agnostic machine learning framework for people who want to write portable, production ready machine learning pipelines. It offers a convenient API to convert a Kedro pipeline to a ``model`` in the mlflow sense. Consequently, you can *API-fy* or serve your Kedro pipeline with one line of code, or share a model with without worrying of the preprocessing to be made for further use. This is directly linked to [Mlflow Models](https://www.mlflow.org/docs/latest/models.html).

# How do I install kedro-mlflow?

**Important: ``kedro-mlflow`` is only compatible with ``kedro>=0.16.0`` and ``mlflow>=1.0.0``. If you have a project created with an older version of ``Kedro``, see this [migration guide](https://github.com/quantumblacklabs/kedro/blob/master/RELEASE.md#migration-guide-from-kedro-015-to-016).**

``kedro-mlflow`` is available on PyPI, so you can install it with ``pip``:

```console
pip install kedro-mlflow
```

If you want to use the most up to date version of the package which is under development and not released yet, you can install the package from github:

```console
pip install --upgrade git+https://github.com/Galileo-Galilei/kedro-mlflow.git
```

I strongly recommend to use ``conda`` (a package manager) to create an environment and to read [``kedro`` installation guide](https://kedro.readthedocs.io/en/latest/get_started/install.html).

# Getting started

The documentation contains:

- [A  "hello world" example](https://kedro-mlflow.readthedocs.io/en/latest/source/03_getting_started/index.html) which demonstrates how you to **setup your project**, **version parameters** and **datasets**, and browse your runs in the UI.
- A section for [advanced machine learning versioning](https://kedro-mlflow.readthedocs.io/en/latest/source/04_experimentation_tracking/index.html) to show more advanced features (mlflow configuration through the plugin, package and serve a kedro ``Pipeline``...)
- A section to demonstrate how to use `kedro-mlflow` as a [machine learning framework](https://kedro-mlflow.readthedocs.io/en/latest/source/05_framework_ml/index.html) to deliver production ready pipelines and serve them. This section comes with [an example repo](https://github.com/Galileo-Galilei/kedro-mlflow-tutorial) you can clone and try out.

Some frequently asked questions on more advanced features:

- You want to log additional metrics to the run? -> [Try ``MlflowMetricsDataSet``](https://kedro-mlflow.readthedocs.io/en/stable/source/04_experimentation_tracking/05_version_metrics.html) !
- You want to log nice dataviz of your pipeline that you register with ``MatplotlibWriter``? -> [Try ``MlflowArtifactDataSet`` to log any local files (.png, .pkl, .csv...) *automagically*](https://kedro-mlflow.readthedocs.io/en/stable/source/04_experimentation_tracking/03_version_datasets.html)!
- You want to create easily an API to share your awesome model to anyone? -> [See if ``pipeline_ml_factory`` can fit your needs](https://github.com/Galileo-Galilei/kedro-mlflow/issues/16)
- You want to do something that is not straigthforward with current implementation? Open an issue, and let's see what happens!

# Release and roadmap

The [release history](https://github.com/Galileo-Galilei/kedro-mlflow/blob/master/CHANGELOG.md) centralizes packages improvements across time. The main features coming in next releases are [listed on github milestones](https://github.com/Galileo-Galilei/kedro-mlflow/milestones). Feel free to upvote/downvote and discuss prioritization in associated issues.

# Disclaimer

This package is still in active development. We use [SemVer](https://semver.org/) principles to version our releases. Until we reach `1.0.0` milestone, breaking changes will lead to `<minor>` version number increment, while releases which do not introduce breaking changes in the API will lead to `<patch>` version number increment.

The user must be aware that we will not reach `1.0.0` milestone before Kedro does (mlflow has already reached `1.0.0`). **That said, the API is considered as stable from 0.8.0 version and user can reliably consider that no consequent breaking change will happen unless necessary for Kedro compatibility (e.g. for minor or major Kedro version).**

If you want to migrate from an older version of `kedro-mlflow` to most recent ones, see the [migration guide](https://kedro-mlflow.readthedocs.io/en/stable/source/02_installation/03_migration_guide.html).


# Can I contribute?

We'd be happy to receive help to maintain and improve the package. Any PR will be considered (from typo in the docs to core features add-on) Please check the [contributing guidelines](https://github.com/Galileo-Galilei/kedro-mlflow/blob/master/CONTRIBUTING.md).

# Main contributors

The following people actively maintain, enhance and discuss design to make this package as good as possible:

- [Yolan Honoré-Rougé](https://github.com/galileo-galilei)
- [Takieddine Kadiri](https://github.com/takikadiri)

Many thanks to [Adrian Piotr Kruszewski](https://github.com/akruszewski) for his past work on the repo.
