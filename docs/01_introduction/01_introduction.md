# What is ``Kedro``?

``Kedro`` is a python package which facilitates the prototyping of data pipelines. It aims at implementing software engineering best practices (separation between I/O and compute, abstraction, templating...). It is specifically useful for machine learning projects since it provides within the same interface both interactive objects for the exploration phase and *Command Line Interface* (CLI) and configuration files for the production phase. This makes the transition from exploration to production as smooth as possible.

For more details, see [Kedro's official documentation](https://kedro.readthedocs.io/en/stable/01_introduction/01_introduction.html).

# What is ``Mlflow``?

``Mlflow`` is a library which helps managing the lifecycle of machine learning models. Mlflow provides 4 modules :
- ``Mlflow Tracking`` : This modules focuses on experiment versioning. The goal all the objects needed to reproduce any code execution. This includes code through version control, but also parameters and artifacts (i.e objects fitted on data like encoders, binarizers...). These elements vary wildly during machine learning experimentation phase. ``Mlflow`` also enable to track metrics to evaluate runs, and provides a *User Interface* (UI) to browse the different runs and comapre them.
- ``Mlflow Projects``: This module provides a configuration files and CLI to enable reproducible execution of pipelines in production phase.
- ``Mlflow Models``: This module defines a standard way for packaging machine learning models, and provides built-in ways to serve registered models. Such standardization enable to serve these models across a wide range of tools.
- ``Mlflow Model Registry``: This modules aims at monitoring deployed models. The registry manages the transition between different versions of the same model (when the dataset is retrained on new data, or when parameters are updated) while is is in production.

For more details, see [Mlflow's official documentation](https://www.mlflow.org/docs/latest/index.html).

# A brief comparison between ``Kedro`` and ``Mlflow``

While ``Kedro`` and ``Mlflow`` do not compete in the same field, they provide some overlapping functionalities. ``Mlflow`` is specifically dedicated to machine learning and its lifecycle management, while ``Kedro`` focusing on data pipeline development. Below chart compare the different functionalities

|Functionality |Kedro          |Mlflow         |
|:-------------|:--------------|:--------------|
|I/O abstraction | various ``AbstractDataSet`` | N/A |
|I/O configuration files |- ``catalog.yml`` <br> - ``parameters.yml``          |``MLproject``|
|Compute abstraction|- ``Pipeline`` <br> - ``Node``| N/A |
|Compute configuration files|- ``pipeline.py`` <br> - ``run.py``| `MLproject` |
|Parameters and data versioning| - ``Journal`` <br> - ``AbstractVersionedDataSet`` |- ``log_metric``<br> - ``log_artifact``<br> - ``log_param``|
|Cli execution|command ``kedro run``|command ``mlflow run``|
|Code packaging|command ``kedro package``|N/A|
|Model packaging|N/A|- ``Mlflow Models`` (``mlflow.XXX.log_model`` functions) <br> - ``Mlflow Flavours``|
|Model service|N/A |commands ``mlflow models {serve/predict/deploy}``|
