import mlflow
import re
from typing import Any, Dict

from kedro.hooks import hook_impl
from kedro.io import DataCatalog
from kedro.pipeline import Pipeline
from kedro.pipeline.node import Node

class MlflowNodeSpecs:

    def __init__(self,
                 flatten_dict_params: bool = False,
                 recursive: bool = True,
                 sep: str = "."):
        self.flatten = flatten_dict_params
        self.recursive = recursive
        self.sep = sep

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
        
        # only parameters xwill be logged. Artifacts must be declared manually in the catalog
        params_inputs = {}
        for k, v in inputs.items():
            if k.startswith("params:"):
                params_inputs[k[7:]] = v
            elif k=="parameters":
                params_inputs[k] = v
        
        # dictionnary parameters may be flattened for readibility
        if self.flatten:
            params_inputs = flatten_dict(d=params_inputs,
                                         recursive=self.recursive,
                                         sep=self.sep)

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


if __name__=="__main__":
    inputs={
        "a":1,
        "params:b":2,
        "parameters":3,
        "parameters_3":4,
        "params":4,
        "params:dict_param": dict(a=1,b=2, c=dict(c=3,d=4, e=dict(f=6,g=7)))
    }

    flatten_dict(inputs, recursive=True, sep=".")
    flatten_dict(inputs, recursive=False, sep=".")
