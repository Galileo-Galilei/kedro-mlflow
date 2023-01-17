# How to use `kedro-mlflow` in a notebook

```{important}
You need to install ``ipython`` to access notebook functionalities.
```

## Reminder on mlflow's limitations with interactive use

Data science project lifecycle are very iterative. Mlflow intends to track parameters changes to improve reproducibility. However, one must be conscious that being able to **execute functions outside of a end to end pipeline** puts a strong burden on the user shoulders **because he is in charge to make the code execution coherent** by running the notebooks cells in the right order. Any back and forth during execution to change some parameters in a previous notebook cells and then retrain a model creates an operational risk that the recorded parameter stored in mlflow is different than the real parameter used for training the model.

To make a long story short: **forget about efficient reproducibility** when using mlflow interactively.

It may **still be useful to track some experiments results** especially if they are long to run and vary wildly with parameters, e.g. if you are performing hyperparameter tuning.

These limitations are inherent to the data science process, not to mlflow itself or the plugin.

## Setup mlflow configuration in your notebook

Open your notebook / ipython session with the Kedro CLI:

```bash
kedro jupyter notebook
```


Or if you are on JupyterLab,

```notebook
%load_ext kedro.ipython
```

Kedro [creates a bunch of global variables](https://kedro.readthedocs.io/en/stable/tools_integration/ipython.html#use-kedro-with-ipython-and-jupyter), including a `session`, a ``context`` and a ``catalog`` which are automatically accessible.

When the context was created, ``kedro-mlflow`` automatically:
- loaded and setup (create the tracking uri, export credentials...) the mlflow configuration of your `mlflow.yml`
- import ``mlflow`` which is now accessible in your notebook

If you change your ``mlflow.yml``, reload the kedro extension for the changes to take effect.

## Difference with running through the CLI

- The DataSets `load` and `save` methods works as usual. You can call `catalog.save("my_artifact_dataset", data)` inside a cell, and your data will be logged in mlflow properly (assuming "my_artifact_dataset" is a `kedro_mlflow.io.MlflowArtifactDataSet`).
- The `hooks` which automatically save all parameters/metrics/artifacts in mlflow will work if you run the session interactively, e.g.:

```python
session.run(
    pipeline_name="my_ml_pipeline",
    tags="training",
    from_inputs="data_2",
    to_outputs="data_7",
)
```
but it is not very likely in a notebook.
- if you need to interact manually with the mlflow server, you can use ``context.mlflow.server._mlflow_client``.

## Guidelines and best practices suggestions

During experimentation phase, you will likely not run entire pipelines (or sub pipelines filtered out between some inputs and outputs). Hence, you cannot benefit from Kedro's ``hooks`` (and hence from ``kedro-mlflow`` tracking). From this moment on, perfect reproducbility is impossible to achieve: there is no chance that you manage to maintain a perfectly linear workflow, as you will go back and forth modifying parameters and code to create your model.

I suggest to :
- **focus on versioning parameters and metrics**. The goal is to finetune your hyperparameters and to be able to remember later the best setup. It is not very important to this stage to version all parameters (e.g. preprocessing ones) nor models (after all you will need an entire pipeline to predict and it is very unlikely that you will need to reuse these experiment models one day.) It may be interesting to use ``mlflow.autolog()`` feature to have a easy basic setup.
- **transition quickly to kedro pipelines**. For instance, when you preprocessing is roughly defined, try to put it in kedro pipelines. You can then use notebooks to experiment / perfom hyperparameter tuning while keeping preprocessing "fixed" to enhance reproducibility. You can run this pipeline interactively with :

```python
res = session.run(
    pipeline_name="my_preprocessing_pipeline",
    tags="training",
    from_inputs="data_2",
    to_outputs="data_7",
)
```

``res`` is a python dict with the outputs of your pipeline (e.g. a "preprocessed_data" ``pandas.DataFrame``), and you can use it interactively in your notebook.
