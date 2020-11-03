from typing import Any, Dict

import mlflow
from kedro.framework.context import load_context
from kedro.framework.hooks import hook_impl
from kedro.io import DataCatalog
from kedro.pipeline import Pipeline
from kedro.pipeline.node import Node

from kedro_mlflow.framework.context import get_mlflow_config


class MlflowNodeHook:
    def __init__(self):
        self.context = None
        self.flatten = False
        self.recursive = True
        self.sep = "."

    @hook_impl
    def before_pipeline_run(
        self, run_params: Dict[str, Any], pipeline: Pipeline, catalog: DataCatalog
    ) -> None:
        """Hook to be invoked before a pipeline runs.
        Args:
            run_params: The params needed for the given run.
                Should be identical to the data logged by Journal.
                # @fixme: this needs to be modelled explicitly as code, instead of comment
                Schema: {
                    "run_id": str,
                    "project_path": str,
                    "env": str,
                    "kedro_version": str,
                    "tags": Optional[List[str]],
                    "from_nodes": Optional[List[str]],
                    "to_nodes": Optional[List[str]],
                    "node_names": Optional[List[str]],
                    "from_inputs": Optional[List[str]],
                    "load_versions": Optional[List[str]],
                    "pipeline_name": str,
                    "extra_params": Optional[Dict[str, Any]],
                }
            pipeline: The ``Pipeline`` that will be run.
            catalog: The ``DataCatalog`` to be used during the run.
        """

        self.context = load_context(
            project_path=run_params["project_path"],
            env=run_params["env"],
            extra_params=run_params["extra_params"],
        )
        config = get_mlflow_config(self.context)
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


mlflow_node_hook = MlflowNodeHook()


def flatten_dict(d, recursive: bool = True, sep="."):
    def expand(key, value):
        if isinstance(value, dict):
            new_value = flatten_dict(value) if recursive else value
            return [(key + sep + k, v) for k, v in new_value.items()]
        else:
            return [(key, value)]

    items = [item for k, v in d.items() for item in expand(k, v)]

    return dict(items)
