# Cli commands

## ``init``

 ``kedro mlflow init``: this command is needed to initalize your project. You cannot run any other commands before you run this one once. It performs 2 actions:
    - creates a ``mlflow.yml`` configuration file in your ``conf/local`` folder
    - replace the ``src/PYTHON_PACKAGE/run.py`` file by an updated version of the template. If your template has been modified since project creation, a warning will be raised. You can either run ``kedro mlflow init --force`` to ignore this warning (but this will erase your ``run.py``) or [set hooks manually](../02_installation/02_setup.md#declaring-kedro-mlflow-hooks).

`init` has two arguments:

- `--env` which enable to specifiy another environment where the mlflow.yml should be created (e.g, `base`)
- `--force` which overrides the `mlflow.yml` if it already exists and replaces it with the default one. Use it with caution!

## ``ui``

``kedro mlflow ui``: this command opens the mlflow UI (basically launches the ``mlflow ui`` command )

`ui` accepts the port and host arguments of [``mlflow ui`` command](https://www.mlflow.org/docs/latest/cli.html#mlflow-ui). The default values used will be the ones defined in the [``mlflow.yml`` configuration file under the `ui`](../04_experimentation_tracking/01_configuration.md#configure-the-user-interface).

If you provide the arguments at runtime, they wil take priority over the ``mlflow.yml``, e.g. if you have:

```yaml
# mlflow.yml
ui:
    localhost: "0.0.0.0"
    port: "5001"
```

then

```console
kedro mlflow ui --port=5002
```

will open the ui on port 5002.

## ``modelify``

``kedro mlflow modelify``: this command converts a kedro pipeline to a mlflow model and logs it in mlflow. It enables distributing the kedro pipeline as a standalone model and leverages all mlflow serving capabilities (as an API).

`modelify` accepts the following arguments :

- ``--pipeline``, ``-p``: The name of the kedro pipeline name registered in ``pipeline_registry.py`` that you want to convert to a mlflow model.
- ``--input-name``, ``-i``: The name of the kedro dataset (in ``catalog.yml``)  which is the input of your pipeline. It contains the data to predict on.  
- ``--infer-signature`` :  A boolean which indicates if the signature of the input data should be inferred for mlflow or not.
- ``--infer-input-example`` : A boolean which indicates if the input_example of the input data should be inferred for mlflow or not
- ``--run-id``, ``-r`` : The id of the mlflow run where the model will be logged. If unspecified, the command creates a new run.
- ``--run-name``: The name of the mlflow run where the model will be logged. Defaults to ``"modelify"``.
- ``--copy-mode`` : The copy mode to use when replacing each dataset by a ``MemoryDataset``. Either a string (applied all datasets) or a dict mapping each dataset to a ``copy_mode``.
- ``--artifact-path"`` : The artifact path of mlflow.pyfunc.log_model, see https://www.mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#mlflow.pyfunc.log_model
- ``--code-path`` : The code path of mlflow.pyfunc.log_model, see https://www.mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#mlflow.pyfunc.log_model
- ``--conda-env`` : "The conda environment of mlflow.pyfunc.log_model, see https://www.mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#mlflow.pyfunc.log_model
- ``--registered-model-name`` : The registered_model_name of mlflow.pyfunc.log_model, see https://www.mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#mlflow.pyfunc.log_model
- ``--await-registration-for``: The await_registration_for of mlflow.pyfunc.log_model, see https://www.mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#mlflow.pyfunc.log_model*
- ``--pip-requirements`` : The pip_requirements of mlflow.pyfunc.log_model, see https://www.mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#mlflow.pyfunc.log_model
- ``--extra-pip-requirements`` : The extra_pip_requirements of mlflow.pyfunc.log_model, see https://www.mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#mlflow.pyfunc.log_model
