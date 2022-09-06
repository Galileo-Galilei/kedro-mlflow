# Initialize your Kedro project

This section assume that [you have installed `kedro-mlflow` in your virtual environment](./01_installation.md).

## Create a kedro project

This plugin must be used in an existing kedro project. If you do not have a kedro project yet, you can create it with ``kedro new`` command. [See the kedro docs for a tutorial](https://kedro.readthedocs.io/en/latest/get_started/new_project.html).

If you do not have a real-world project, you can use a kedro example and [follow the "Getting started" example](../03_getting_started/01_example_project.md) to make a demo of this plugin out of the box.

## Activate `kedro-mlflow` in your kedro project

In order to use the ``kedro-mlflow`` plugin, you need to setup its configuration and declare its hooks. Those 2 actions are detailled in the following paragraphs.

### Setting up the ``kedro-mlflow`` configuration file


``kedro-mlflow`` is [configured](../07_python_objects/05_Configuration.md) through an ``mlflow.yml`` file. The recommended way to initialize the `mlflow.yml` is by using [the ``kedro-mlflow`` CLI](../07_python_objects/04_CLI.md), but you can create it manually.

```{note}
Since ``kedro-mlflow>=0.11.2``, the configuration file is optional. However, the plugin will use default ``mlflow`` configuration. Specifically, the runs will be stored in a ``mlruns`` folder at the root fo the kedro project since no ``mlflow_tracking_uri`` is configured.
```

Set the working directory at the root of your kedro project:

```console
cd path/to/your/project
```

Run the init command :

```console
kedro mlflow init
```

you should see the following message:

```console
'conf/local/mlflow.yml' successfully updated.
```

*Note: you can create the configuration file in another kedro environment with the `--env` argument:*

```console
kedro mlflow init --env=<other-environment>
```

### Declaring ``kedro-mlflow`` hooks

``kedro_mlflow`` hooks implementations must be registered with Kedro. There are 2 ways of registering [hooks](https://kedro.readthedocs.io/en/latest/hooks/introduction.html).

**Note that you must register the hook provided by kedro-mlflow** (``MlflowHook``) to make the plugin work.

#### Declaring hooks through auto-discovery (for `kedro>=0.16.4`) [Default behaviour]

If you use `kedro>=0.16.4`, `kedro-mlflow` hooks are auto-registered automatically by default without any action from your side. You can [disable this behaviour](https://kedro.readthedocs.io/en/latest/hooks/introduction.html#disable-auto-registered-plugins-hooks) in your `settings.py` file.

#### Declaring hooks statically in settings.py

If you have turned off plugin automatic registration, you can register its hooks manually by [adding them to ``settings.py``](https://kedro.readthedocs.io/en/latest/hooks/introduction.html#registering-your-hook-implementations-with-kedro):

```python
# <your_project>/src/<your_project>/settings.py
from kedro_mlflow.framework.hooks import MlflowHook

HOOKS = (MlflowHook(),)
```
