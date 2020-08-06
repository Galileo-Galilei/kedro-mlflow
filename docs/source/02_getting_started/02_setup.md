# Setup your Kedro project
## Create a kedro project
This plugins must be used in an existing kedro project. If you do not have a kedro project yet, you can create it with ``kedro new`` command. [See the kedro docs for a tutorial](https://kedro.readthedocs.io/en/latest/02_getting_started/03_new_project.html).

For this tutorial and if you do not have a real-world project, I strongly suggest that you accept to include the proposed example to make a demo of this plugin out of the box.

## Update the template of your kedro project
In order to use the ``kedro-mlflow`` plugin, you need to perform 2 actions:
1. Create an ``mlflow.yml`` file for [configuring mlflow in a dedicated file](../04_python_objects/configuration.md).
2. Update the ``src/PYTHON_PACKAGE/run.py`` to add the [necessary hooks](../04_python_objects/hooks.md) to the project context. The ``MlflowPipelineHook`` manages the configuration and registers the PipelineML, while the ``MlflowNodeHook`` autolog the parameters.
## Automatic template update (recommended)
### Default situation
The first and recommended possibility to setup this context is to use a [dedicated command line](../04_python_objects/cli_commands.md) offered by the plugin.
Position yourself with at the root (i.e. the folder with the ``.kedro.yml`` file)

```bash
$ cd path/to/your/project
```

Run the init command :

```bash
$ kedro mlflow init
```

*Note : If the warning ``"You have not updated your template yet. This is mandatory to use 'kedro-mlflow' plugin. Please run the following command before you can access to other commands : '$ kedro mlflow init'`` is raised, this is a bug to be corrected and you can safely ignore it.*
If you have never modified your ``run.py`` manually, it should run smoothly and you should get the following message:
```bash
'conf/base/mlflow.yml' successfully updated.
'run.py' successfully updated
```

### Special case: what happens if you have a custom ``run.py`` ?

You may have modified the ``run.py`` manually since the creation of the project. This may happen in the following situations:
- you have added ``hooks`` (of another plugin for instance)
- you have modified the ``ConfigLoader``, for instance to us a ``TemplatedConfigLoader`` to make your configuration dynamic and link the files with one another
- you have modified the ``get_pipelines`` functions to implement specific logic
-...
These are advanced features of ``Kedro`` and it if you have made such modifications they are very likely conscious; however some other plugins may have modified this file without any warning.

Whatever the reason is, if you ``run.py`` was modified since the project creation, the [previous process](#default-situation) will return the following warning message:
```bash
You have modified your 'run.py' since project creation.
In order to use kedro-mlflow, you must either:
    -  set up your run.py with the following instructions :
INSERT_DOC_URL
    - call the following command:
$ kedro mlflow init --force
```
In this situation, the ``mlflow.yml`` is still created, but the ``run.py`` is left unchanged to avoid messing up with your own changes. You can still erase your ``run.py`` and replace it with the one of the plugin with below command.

```bash
kedro mlflow init --force
```
**USE AT YOUR OWN RISK: This will erase definitely all the modifications you made to your own ``run.py`` with no possible recovery.** In consequence, this is not the recommended way to setup the project if you have a custom ``run.py``. The best way to continue the setup is to [set up the hooks manually](#manual-update).

## Manual update

The ``MlflowPipelineHook`` and ``MlflowNodeHook`` hooks need to be registered in the the ``run.py`` file. The kedro documenation explain sinde tail [how to register a hook](https://kedro.readthedocs.io/en/latest/04_user_guide/15_hooks.html#registering-your-hook-implementations-with-kedro).

Your run.py should look like the following code snippet :

```python
from kedro_mlflow.framework.hooks import MlflowNodeHook, MlflowPipelineHook
from YOUR_PYTHON_PACKAGE.pipeline import create_pipelines

class ProjectContext(KedroContext):
    """Users can override the remaining methods from the parent class here,
    or create new ones (e.g. as required by plugins)
    """

    project_name = "YOUR PROJECT NAME"
    project_version = "0.16.2"
    hooks = (
        MlflowNodeHook(flatten_dict_params=False),
        MlflowPipelineHook(model_name="YOUR_PYTHON_PACKAGE",
                           conda_env="src/requirements.txt")
    )  # <-- the new lines to add
```

Pay attention to the following elements:
- if you have other hooks (custom, from other plugins...), you can just add them to the hooks tuple
- you **must register both hooks** for the plugin to work
- the hooks are highly parametrizable, you can find a [detailed description of their parameters here](../04_python_objects/hooks.md).
