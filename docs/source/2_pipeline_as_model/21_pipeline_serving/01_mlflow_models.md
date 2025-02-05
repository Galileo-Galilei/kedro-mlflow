# Introduction to mlflow models

## What are Mlflow Models ?

[Mlflow Models are a standardised agnostic format to store machine learning models](https://www.mlflow.org/docs/latest/models.html). They intend to be standalone to be as portable as possible to be deployed virtually anywhere and mlflow provides built-in CLI commands to deploy a mlflow model to most common cloud platforms or to create an API.

A Mlflow Model is composed of:

- a ``MLModel`` file which is a configuration file to indicate to mlflow how to load the model. This file may also contain the ``Signature`` of the model (i.e. the ``Schema`` of the input and output of your model, including the columns names and order) as well as example data.  
- a ``conda.yml`` file which contains the specifications of the virtual conda environment inside which the model should run. It contains the packages versions necessary for your model to be executed.
- a ``model.pkl`` (or a ``python_function.pkl`` for custom model) file containing the trained model.  
- an ``artifacts`` folder containing all other data necessary to execute the models

```{important}
Mlflow enable to create **custom models "flavors" to convert any object to a Mlflow Model** provided we have these informations. Inside a Kedro project, the ``Pipeline`` and ``DataCatalog`` objects contain all these informations. As a consequence, it is easy to create a custom model to convert entire Kedro ``Pipeline``s to mlflow models, and it the purpose of ``pipeline_ml_factory`` and ``KedroPipelineModel`` that we will present in the following sections.
```

## Pre-requisite for converting a pipeline to a mlflow model

You can log any Kedro ``Pipeline`` matching the following requirements:

- one of its input must be a ``pandas.DataFrame``, a ``spark.DataFrame`` or a ``numpy.array``. This is the **input which contains the data to predict on**. This can be any Kedro ``AbstractDataset`` which loads data in one of the previous three formats. It can also be a ``MemoryDataset`` and not be persisted in the ``catalog.yml``.
- all its other inputs must be persisted on disk (e.g. if the machine learning model must already be trained and saved so we can export it) or declared as "parameters" in the model ``Signature``.

```{warning}
If the pipeline has parameters :
- For ``mlflow<2.7.0`` the parameters need to be persisted before exporting the model, which implies that you will not be able to modify them at runtime. This is a limitation of ``mlflow<2.6.0``
- For ``mlflow>=2.7.0`` , they can be declared in the signature and modified at runtime. See https://github.com/Galileo-Galilei/kedro-mlflow/issues/445 for more information.
```
