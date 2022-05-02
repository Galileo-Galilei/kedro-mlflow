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
