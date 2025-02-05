```kedro-mlflow``` is a Kedro [plugin](https://docs.kedro.org/en/stable/extend_kedro/plugins.html) to integrate [MLflow](https://www.mlflow.org/) effortlessly inside [Kedro](https://kedro.org/) projects.

## Key Features

Its main features are **automatic parameters tracking**, **datasets tracking as artifacts**, Kedro **pipelines packaging** and serving and **automatic synchronisation between training and inference** pipelines. It aims at providing a complete yet modular framework for high reproducibility of machine learning experiments and ease of deployment.

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card}
:link: source/1_experiment_tracking/10_experiment_tracking/01_configuration.html
:link-type: url
:class-header: bg-light

{fas}`flask fa-xl;pst-color-primary` Experiment tracking
^^^

Track the **parameters**, **metrics**, **artifacts** and **models** of your kedro pipelines for reproducibility.
:::

:::{grid-item-card}
:link:
:link-type: url
:class-header: bg-light

{fas}`rocket fa-xl;pst-color-primary` Pipeline as model
^^^

Package any kedro pipeline to a **custom mlflow model** for deployment and serving. The custom model for an inference pipeline can be **registered** in mlflow **automatically** at the end of each training in a *scikit-learn* like way.
:::

::::

## Resources

::::{grid} 1 1 3 3
:gutter: 3

:::{grid-item-card}
:link: source/0_getting_started/02_installation/01_installation.html
:link-type: url
:class-header: bg-light

{fas}`book fa-xl;pst-color-primary` Quickstart
^^^

Get started in **1 mn** with experiment tracking!
+++
Try out {fas}`arrow-right fa-xl`
:::

:::{grid-item-card}
:link: https://github.com/Galileo-Galilei/kedro-mlflow-tutorial
:link-type: url
:class-header: bg-light

{fas}`fa-solid fa-chalkboard-user fa-xl;pst-color-primary` Advanced tutorial
^^^

The ``kedro-mlflow-tutorial`` github repo contains a step-by-step tutorial to learn how to use kedro-mlflow as a mlops framework!

+++
Try on github {fab}`github;fa-xl`
:::

:::{grid-item-card}
:link: https://www.youtube.com/watch?v=Az_6UKqbznw
:link-type: url
:class-header: bg-light

{fas}`fa-solid fa-video fa-xl;pst-color-primary` Demonstration in video
^^^

A youtube video by the kedro team to introduce the plugin, with live coding.

+++
See on youtube {fab}`youtube;fa-xl`
:::

::::

```{toctree}
---
maxdepth: 1
hidden: true
---
source/01_introduction/index
source/02_getting_started/index
source/03_experiment_tracking/index
source/04_pipeline_as_model/index
source/05_API/index
```
