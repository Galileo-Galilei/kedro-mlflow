# Introduction to ``kedro`` and ``mlflow``

## What is ``Kedro``?

``Kedro`` is a python package which facilitates the prototyping of data pipelines. It aims at enforcing software engineering best practices (separation between I/O and compute, abstraction, templating...). It is specifically useful for machine learning projects since it provides within the same interface interactive objects for the exploration phase, and *Command Line Interface* (CLI) and configuration files for the production phase. This makes the transition from exploration to production as smooth as possible.

For more details, see [Kedro's official documentation](https://docs.kedro.org/en/stable/introduction/index.html).

## What is ``Mlflow``?

``Mlflow`` is a library which manages the lifecycle of machine learning models. Mlflow provides 4 modules:

- [``Mlflow Tracking``](https://www.mlflow.org/docs/latest/tracking.html): This modules focuses on experiment versioning. Its goal is to store all the objects needed to reproduce any code execution. This includes code through version control, but also parameters and artifacts (i.e objects fitted on data like encoders, binarizers...). These elements vary wildly during machine learning experimentation phase. ``Mlflow`` also enable to track metrics to evaluate runs, and provides a *User Interface* (UI) to browse the different runs and compare them.
- [``Mlflow Projects``](https://www.mlflow.org/docs/latest/projects.html): This module provides a configuration files and CLI to enable reproducible execution of pipelines in production phase.
- [``Mlflow Models``](https://www.mlflow.org/docs/latest/models.html): This module defines a standard way for packaging machine learning models, and provides built-in ways to serve registered models. Such standardization enable to serve these models across a wide range of tools.
- [``Mlflow Model Registry``](https://www.mlflow.org/docs/latest/model-registry.html): This modules aims at monitoring deployed models. The registry manages the transition between different versions of the same model (when the dataset is retrained on new data, or when parameters are updated) while it is in production.

For more details, see [Mlflow's official documentation](https://www.mlflow.org/docs/latest/index.html).

## A brief comparison between ``Kedro`` and ``Mlflow``

While ``Kedro`` and ``Mlflow`` do not compete in the same field, they provide some overlapping functionalities. ``Mlflow`` is specifically dedicated to machine learning and its lifecycle management, while ``Kedro`` focusing on data pipeline development. Below chart compare the different functionalities:

| Functionality                  | Kedro                                             | Mlflow                                                                              |
| :----------------------------- | :------------------------------------------------ | :---------------------------------------------------------------------------------- |
| I/O abstraction                | various ``AbstractDataset``                       | N/A                                                                                 |
| I/O configuration files        | - ``catalog.yml`` <br> - ``parameters.yml``       | ``MLproject``                                                                       |
| Compute abstraction            | - ``Pipeline`` <br> - ``Node``                    | N/A                                                                                 |
| Compute configuration files    | - ``hooks.py`` <br> - ``run.py``                  | `MLproject`                                                                         |
| Parameters and data versioning | - ``Journal`` (deprecated) <br> - Experiment tracking (deprecated) <br> - ``AbstractVersionedDataset`` | - ``log_metric``<br> - ``log_artifact``<br> - ``log_param``|
| Cli execution                  | command ``kedro run``                             | command ``mlflow run``                                                              |
| Code packaging                 | command ``kedro package``                         | N/A                                                                                 |
| Model packaging                | N/A                                               | - ``Mlflow Models`` (``mlflow.XXX.log_model`` functions) <br> - ``Mlflow Flavours`` |
| Model service                  | N/A                                               | commands ``mlflow models {serve/predict/deploy}``                                   |

We discuss hereafter how the two libraries compete on the different functionalities and eventually complete each others.

### Configuration and prototyping: Kedro 1 - 0 Mlflow

``Mlflow`` and ``Kedro`` are essentially overlapping on the way they offer a dedicated configuration files for running the pipeline from CLI. However:  

- ``Mlflow`` provides a single configuration file (the ``MLProject``) where all elements are declared (data, parameters and pipelines). Its goal is mainly to enable CLI execution of the project, but it is not very flexible. This file is **production oriented** and is not really intended to use for  and development.
- ``Kedro`` offers a bunch of files (``catalog.yml``, ``parameters.yml``, ``pipeline.py``) and their associated abstraction (``AbstractDataset``, ``DataCatalog``, ``Pipeline`` and ``node`` objects). ``Kedro`` is much more opinionated: each object has a dedicated place (and only one!) in the template. This makes the framework both **exploration and production oriented**. The downside is that it could make the learning curve a bit sharper since a newcomer has to learn all ``Kedro`` specifications. It also provides a ``kedro-viz`` plugin to visualize the DAG interactively, which is particularly handy in medium-to-big projects.


```{note}
**``Kedro`` is a clear winner here, since it provides more functionnalities than ``Mlflow``. It handles very well _by design_ the exploration phase of data science projects when Mlflow is less flexible.**
```

### Versioning: Kedro 1 - 1 Mlflow

Kedro ahas made a bunch of attempts in the world of experiment tracking, with the ``Journal`` in early days (``kedro<=0.18``), then with an [experiment tracking functionality](https://docs.kedro.org/projects/kedro-viz/en/v9.2.0/experiment_tracking.html) which kept track of the parameters but which will be removed in ``kedro>=0.20`` due to the lack of traction (https://github.com/kedro-org/kedro-viz/issues/2202).

On the other hand, ``Mlflow``:

- distinguishes between artifacts (i.e. any data file), metrics (integers that may evolve over time) and parameters. The logging is very straightforward since there is a one-liner function for logging the desired type. This separation makes further manipulation easier.
- offers a way to configure the logging in a database through the ``mlflow_tracking_uri`` parameter. This database-like logging comes with easy [querying of different runs through a client](https://www.mlflow.org/docs/latest/python_api/mlflow.client.html#mlflow.client.MlflowClient) (for instance "find the most recent run with a metric at least above a given threshold" is immediate with ``Mlflow`` but hacky in ``Kedro``).
- [comes with a *User Interface* (UI)](https://mlflow.org/docs/latest/tracking.html#id7) which enable to browse / filter / sort the runs, display graphs of the metrics, render plots... This make the run management much easier than in ``Kedro``.
- has a command to reproduce exactly the run from a given ``git sha``, [which is not possible in ``Kedro``](https://github.com/quantumblacklabs/kedro/issues/297).

```{note}
**``Mlflow`` is a clear winner here, because _UI_ and _run querying_ are must-have for machine learning projects. It is more mature than ``Kedro`` for versioning and more focused on machine learning.**
```

### Model packaging and service: Kedro 1 - 2 Mlflow

``Kedro`` offers a way to package the code to make the pipelines callable, but does not manage specifically machine learning models.

``Mlflow`` offers a way to store machine learning models with a given "flavor", which is the minimal amount of information necessary to use the model for prediction:

- a configuration file
- all the artifacts, i.e. the necessary data for the model to run (including encoder, binarizer...)
- a loader
- a conda configuration through an ``environment.yml`` file

When a stored model meets these requirements, ``Mlflow`` provides built-in tools to serve the model (as an API or for batch prediction) on many machine learning tools (Microsoft Azure ML, Amazon Sagemaker, Apache SparkUDF) and locally.

```{note}
``Mlflow`` is currently the only tool which adresses model serving. Some [plugins address model deployment and serving](https://docs.kedro.org/en/stable/extend_kedro/plugins.html#community-developed-plugins) in the Kedro ecosystem, but they are not as well maintained as the core framework.
```

### Conclusion: Use Kedro and add Mlflow for machine learning projects

``Kedro``'s will to enforce software engineering best practice makes it really useful for machine learning teams. It is extremely well documented and the support is excellent, which makes it very user friendly even for people with no computer science background. However, it lacks some machine learning-specific functionalities (better versioning, model service), and it is where ``Mlflow`` fills the gap.
