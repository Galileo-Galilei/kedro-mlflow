# Motivation

## When should I use kedro-mlflow?

Basically, you should use `kedro-mlflow` in **any `Kedro` project which involves machine learning** / deep learning. As stated in the [introduction](./01_introduction.md), `Kedro`'s current versioning (as of version `0.16.6`) is not sufficient for machine learning projects: it lacks a UI and a ``run`` management system. Besides, the `KedroPipelineModel` ability to serve a kedro pipeline as an API or a batch in one line of code is a great addition for collaboration and transition to production.

If you do not use ``Kedro`` or if you do pure data processing which do not involve *machine learning*, this plugin is not what you are seeking for ;)

## Why should I use kedro-mlflow?

### Benchmark of existing solutions

This paragraph gives a (quick) overview of existing solutions for mlflow integration inside Kedro projects.

``Mlflow`` is very simple to add to any existing code. It is a 2-step process:

- add `log_{XXX}` (either param, artifact, metric or model) functions where they are needed inside the code
- add a `MLProject` at the root of the project to enable CLI execution. This file must contain all the possible execution steps (like the `pipeline.py` / `hooks.py`  in a kedro project).

Including mlflow inside a ``kedro project`` is consequently very easy: the logging functions can be added in the code, and the ``MLProject`` is very simple and is composed almost only of the ``kedro run`` command. You can find examples of such implementations:

- the [medium paper](https://medium.com/quantumblack/deploying-and-versioning-data-pipelines-at-scale-942b1d81b5f5) by QuantumBlack employees.
- the associated [github repo](https://github.com/tgoldenberg/kedro-mlflow-example)
- other examples can be found on Github, but AFAIK all of them follow the very same principles.

### Enforcing Kedro principles

Above implementations have the advantage of being very straightforward and *mlflow compliant*, but they break several ``Kedro`` principles:

- the ``MLFLOW_TRACKING_URI`` which registers the database where runs are logged is declared inside the code instead of a configuration file, which **hinders portability across environments** and makes transition to production more difficult
- the logging of different elements can be put in many places in the ``Kedro`` template (in the code of any function involved in a ``node``, in a ``Hook``, in  the ``ProjectContext``, in a ``transformer``...). This is not compliant with the ``Kedro`` template where any object has a dedicated location. We want to avoid the logging to occur anywhere because:
  - it is **very error-prone** (one can forget to log one parameter)
  - it is **hard to modify** (if you want to remove / add / modify an mlflow action you have to find it in the code)
  - it **prevents reuse** (re-usable function must not contain mlflow specific code unrelated to their functional specificities, only their execution must be tracked).

``kedro-mlflow`` enforces these best practices while implementing a clear interface for each mlflow action in Kedro template. Below chart maps the mlflow action to perform with the Python API provided by ``kedro-mlflow`` and the location in Kedro template where the action should be performed.

| Mlflow action             | Template file   | Python API                                               |
| :------------------------ | :-------------- | :------------------------------------------------------- |
| Set up configuration      | ``mlflow.yml``  | ``MlflowHook``                                           |
| Logging parameters        | ``mlflow.yml``  | ``MlflowHook``                                           |
| Logging artifacts         | ``catalog.yml`` | ``MlflowArtifactDataSet``                                |
| Logging models            | ``catalog.yml`` | `MlflowModelLoggerDataSet` and `MlflowModelSaverDataSet` |
| Logging metrics           | ``catalog.yml`` | ``MlflowMetricsDataSet``                                 |
| Logging Pipeline as model | ``hooks.py``    | ``KedroPipelineModel`` and ``pipeline_ml_factory``       |

`kedro-mlflow` does not currently provide interface to set tags outside a Kedro ``Pipeline``. Some of above decisions are subject to debate and design decisions (for instance, metrics are often updated in a loop during each epoch / training iteration and it does not always make sense to register the metric between computation steps, e.g. as a an I/O operation after a node run).

```{note}
You do **not** need any ``MLProject`` file to use mlflow inside your Kedro project. As seen in the [introduction](./01_introduction.md), this file overlaps with Kedro configuration files.
```
