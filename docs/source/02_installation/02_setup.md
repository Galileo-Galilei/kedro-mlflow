# Initialize your Kedro project

This section assume that [you have installed `kedro-mlflow` in your virtual environment](./01_installation.md).

## Create a kedro project

This plugin must be used in an existing kedro project. If you do not have a kedro project yet, you can create it with ``kedro new`` command. [See the kedro docs for a tutorial](https://kedro.readthedocs.io/en/latest/02_get_started/04_new_project.html).

If you do not have a real-world project, you can use a kedro example and [follow the "Getting started" example](../03_getting_started/01_example_project.md) to make a demo of this plugin out of the box.

## Activate `kedro-mlflow` in your kedro project

In order to use the ``kedro-mlflow`` plugin, you need to setup its configuration and declare its hooks. Those 2 actions are detailled in the following paragraphs.

### Setting up the ``kedro-mlflow`` configuration file

``kedro-mlflow`` is [configured](../07_python_objects/05_Configuration.md) through an ``mlflow.yml`` file. The recommended way to initialize the `mlflow.yml` is by using [the ``kedro-mlflow`` CLI](../07_python_objects/04_CLI.md). **It is mandatory for the plugin to work.**

Set the working directory at the root of your kedro project (i.e. the folder with the ``.kedro.yml`` file)

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

``kedro_mlflow`` hooks implementations must be registered with Kedro. There are three ways of registering [hooks](https://kedro.readthedocs.io/en/latest/07_extend_kedro/02_hooks.html).

**Note that you must register the two hooks provided by kedro-mlflow** (``MlflowPipelineHook`` and ``MlflowNodeHook``) for the plugin to work.

#### Declaring hooks through auto-discovery (for `kedro>=0.16.4`) [Default behaviour]

If you use `kedro>=0.16.4`, `kedro-mlflow` hooks are auto-registered automatically by default without any action from your side. You can [disable this behaviour](https://kedro.readthedocs.io/en/latest/07_extend_kedro/02_hooks.html#disable-auto-registered-plugins-hooks) in your `.kedro.yml` or your `pyproject.toml` file.

#### Declaring hooks through code, in ``ProjectContext`` (for `kedro>=0.16.0, <=0.16.3`)

By declaring `mlflow_pipeline_hook` and `mlflow_node_hook` in ``(src/package_name/run.py) ProjectContext``:

```python
from kedro_mlflow.framework.hooks import mlflow_pipeline_hook, mlflow_node_hook

class ProjectContext(KedroContext):
    """Users can override the remaining methods from the parent class here,
    or create new ones (e.g. as required by plugins)
    """

    project_name = "<project-name>"
    project_version = "0.16.X" # must be >=0.16.0
    hooks = (
        mlflow_pipeline_hook,
        mlflow_node_hook
    )
```

#### Declaring hooks through static configuration in `.kedro.yml` or `pyproject.toml` **[Only for kedro >= 0.16.5 if you have disabled auto-registration]**

In case you have disabled hooks for plugin, you can add them manually by declaring `mlflow_pipeline_hook` and `mlflow_node_hook` in ``.kedro.yml`` :

```yaml
context_path: km_example.run.ProjectContext
project_name: "km_example"
project_version: "0.16.5"
package_name: "km_example"
hooks:
  - <your-project>.hooks.project_hooks
  - kedro_mlflow.framework.hooks.mlflow_pipeline_hook
  - kedro_mlflow.framework.hooks.mlflow_node_hook
```

Or by declaring `mlflow_pipeline_hook` and `mlflow_node_hook` in ``pyproject.toml`` :

```yaml
# <your-project>/pyproject.toml
[tool.kedro]
hooks=["kedro_mlflow.framework.hooks.mlflow_pipeline_hook",
       "kedro_mlflow.framework.hooks.mlflow_node_hook"]
```
