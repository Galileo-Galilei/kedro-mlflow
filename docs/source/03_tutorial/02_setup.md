# Setup your Kedro project

## Check the installation

Type  ``kedro info`` in a terminal to check if the plugin is properly discovered by ``Kedro``. If the installation has succeeded, you should see the following ascii art:

```console
 _            _
| | _____  __| |_ __ ___
| |/ / _ \/ _` | '__/ _ \
|   <  __/ (_| | | | (_) |
|_|\_\___|\__,_|_|  \___/
v<kedro-version>

kedro allows teams to create analytics
projects. It is developed as part of
the Kedro initiative at QuantumBlack.

Installed plugins:
kedro_mlflow: <kedro-mlflow-version> (hooks:global,project)
```

The version ``<kedro-mlflow-version>`` of the plugin is installed ans has both global and project commands.

That's it! You are now ready to go!

## Create a kedro project

This plugins must be used in an existing kedro project. If you do not have a kedro project yet, you can create it with ``kedro new`` command. [See the kedro docs for a tutorial](https://kedro.readthedocs.io/en/latest/02_getting_started/03_new_project.html).

For this tutorial and if you do not have a real-world project, I strongly suggest that you accept to include the proposed example to make a demo of this plugin out of the box.

## Activate `kedro-mlflow` in your kedro project

In order to use the ``kedro-mlflow`` plugin, you need to set up the its configuration and declare its hooks. those 2 actions are detailled in the following paragraph.

### Setting up the kedro-mlflow configuration file

``kedro-mlflow`` is [configured](../05_python_objects/05_Configuration.md) through an ``mlflow.yml`` file. The recommended way to initialize the `mlflow.yml` is by using [the kedro-mlflow CLI](../05_python_objects/04_CLI.md). **It is mandatory for the plugin to work.**

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
'conf/base/mlflow.yml' successfully updated.
```

### Declaring kedro-mlflow hooks

``kedro_mlflow`` hooks implementations must be registered with Kedro. There are three ways of registring [hooks](https://kedro.readthedocs.io/en/latest/07_extend_kedro/04_hooks.html?highlight=hooks).

**Note that you must register the two hooks provided by kedro-mlflow** (``MlflowPipelineHook`` and ``MlflowNodeHook``) for the plugin to work.

#### - Declaring hooks through auto-discovery (for `kedro>=0.16.4`)

If you use `kedro>=0.16.4`, `kedro-mlflow` hooks are auto-registered automatically by default without any action from your side. You can [disable this behaviour](https://kedro.readthedocs.io/en/latest/07_extend_kedro/04_hooks.html#disable-auto-registered-plugins-hooks) in your `.kedro.yml` or your `pyproject.toml` file.

#### - Declaring hooks through code, in ``ProjectContext`` (for `kedro>=0.16.0, <=0.16.3`)

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

#### - Declaring hooks through static configuration in `.kedro.yml` or `pyproject.toml` **[Only for kedro >= 0.16.5 if you have disabled auto-registration]**

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
