from typing import Any, Dict

import mlflow
from kedro.framework.hooks import hook_impl
from kedro.io import DataCatalog
from kedro.pipeline.node import Node

from kedro_mlflow.framework.context import get_mlflow_config


class MlflowNodeHook:
    def __init__(self):
        config = get_mlflow_config()
        self.flatten = config.node_hook_opts["flatten_dict_params"]
        self.recursive = config.node_hook_opts["recursive"]
        self.sep = config.node_hook_opts["sep"]

    @hook_impl
    def before_node_run(
        self,
        node: Node,
        catalog: DataCatalog,
        inputs: Dict[str, Any],
        is_async: bool,
        run_id: str,
    ) -> None:
        """Hook to be invoked before a node runs.
        This hook logs all the paramters of the nodes in mlflow.
        Args:
            node: The ``Node`` to run.
            catalog: A ``DataCatalog`` containing the node's inputs and outputs.
            inputs: The dictionary of inputs dataset.
            is_async: Whether the node was run in ``async`` mode.
            run_id: The id of the run.
        """

        # only parameters will be logged. Artifacts must be declared manually in the catalog
        params_inputs = {}
        for k, v in inputs.items():
            if k.startswith("params:"):
                params_inputs[k[7:]] = v
            elif k == "parameters":
                params_inputs[k] = v

        # dictionary parameters may be flattened for readibility
        if self.flatten:
            params_inputs = flatten_dict(
                d=params_inputs, recursive=self.recursive, sep=self.sep
            )

        mlflow.log_params(params_inputs)


def flatten_dict(d, recursive: bool = True, sep="."):
    def expand(key, value):
        if isinstance(value, dict):
            new_value = flatten_dict(value) if recursive else value
            return [(key + sep + k, v) for k, v in new_value.items()]
        else:
            return [(key, value)]

    items = [item for k, v in d.items() for item in expand(k, v)]

    return dict(items)
