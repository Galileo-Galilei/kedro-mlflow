# The kedro-mlflow plugin

## What is kedro-mlflow ?

```kedro-mlflow``` is a kedro plugin to integrate [MLflow](https://www.mlflow.org/) effortlessly inside [Kedro](https://kedro.org/) projects. It integrates effortlessly within any existing kedro projects. Its main features are automatic parameters tracking, datasets versioning, Kedro pipelines packaging and serving and automatic synchronisation between training and inference pipelines. It aims at providing a complete yet modular framework for high reproducibility of machine learning experiments and ease of deployment.

## What can I do with kedro-mlflow

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card}
:link: https://kedro-mlflow.readthedocs.io/en/stable/source/10_experiment_tracking/index.html
:link-type: url
:class-header: bg-light

{fas}`book;pst-color-primary` Quickstart
^^^

Get started in **1 mn** !
+++
Try out {fas}`arrow-right`
:::

:::{grid-item-card}
:link: https://kedro-mlflow.readthedocs.io/en/stable/source/10_experiment_tracking/index.html
:link-type: url
:class-header: bg-light

{fas}`flask;pst-color-primary` Experiment tracking
^^^

Track the **parameters**, **metrics**, **artifacts** and **models** of your kedro pipelines for reproducibility.
+++
Learn how {fas}`arrow-right`
:::

:::{grid-item-card}
:link: https://kedro-mlflow.readthedocs.io/en/stable/source/21_pipeline_serving/index.html
:link-type: url
:class-header: bg-light

{fas}`rocket;pst-color-primary` Pipeline serving
^^^

Package any kedro pipeline to a **custom mlflow model** for serving. The custom model for an inference pipeline can be **registered** in mlflow **automatically** at the end of each training in a *scikit-learn* like way.
+++
Learn how {fas}`arrow-right`
:::

:::{grid-item-card}
:link: https://github.com/Galileo-Galilei/kedro-mlflow-tutorial
:link-type: url
:class-header: bg-light

{fas}`fa-solid fa-chalkboard-user;pst-color-primary` Advanced tutorial
^^^

The ``kedro-mlflow-tutorial`` github repo contains a step-by-step tutorial to learn how to use kedro-mlflow as a mlops framework!

+++
Try on github {fab}`fa-github`
:::

::::

## What's New?

```{toctree}
---
maxdepth: 1
hidden: true
---
source/0_getting_started/index
source/1_experiment_tracking/index
<!-- source/02_installation/index
source/03_quickstart/index
source/10_experiment_tracking/index
source/11_interactive_use/index
source/21_pipeline_serving/index
source/22_framework_ml/index
source/30_python_objects/index -->
```
