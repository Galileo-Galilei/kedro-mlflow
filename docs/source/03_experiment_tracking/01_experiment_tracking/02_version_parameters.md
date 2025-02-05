# Track parameters

## Automatic parameters tracking

Parameters tracking is automatic when the ``MlflowHook`` is added to [the hook list of the ``ProjectContext``](../../02_getting_started/01_installation/02_setup.html). The `mlflow.yml` configuration file has a parameter called ``flatten_dict_params`` which enables to [log as distinct parameters the (key, value) pairs of a ```Dict`` parameter](../../05_API/01_python_objects/02_Hooks.html).

You **do not need any additional configuration** to benefit from parameters versioning.

```{hint}

**How does ``MlflowHook`` operates under the hood?**

The [medium post which introduces hooks](https://medium.com/quantumblack/introducing-kedro-hooks-fd5bc4c03ff5) explains in detail the steps ``Kedro`` executes when the user calls the ``kedro run`` command.

![](../../imgs/hook_registration_process.png)

The `MlflowHook` registers the parameters before each node (entry point number 3 on above picture) by calling `mlflow.log_parameter(param_name, param_value)` on each parameters of the node.

```

## Frequently asked questions

:::{dropdown} How are parameters detected by the plugin?
The hook **detects parameters through their prefix ``params:`` or the value ``parameters``**. These are the [reserved keywords used by Kedro to define parameters](https://docs.kedro.org/en/stable/configuration/parameters.html#how-to-use-parameters) in the ``pipeline.py`` file(s).
:::

:::{dropdown} Will parameters be recorded if the pipeline fails during execution?
The parameters are registered node by node (and not in a single batch at the beginning of the execution). If the pipeline fails in the middle of its execution, the **parameters of the nodes who have been run will be recorded**, but **not the parameters of non executed nodes**.
:::
