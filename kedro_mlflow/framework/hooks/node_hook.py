import logging
from typing import Any, Dict, Union

import mlflow
from kedro.framework.hooks import hook_impl
from kedro.io import DataCatalog
from kedro.pipeline import Pipeline
from kedro.pipeline.node import Node
from mlflow.utils.validation import MAX_PARAM_VAL_LENGTH

from kedro_mlflow.config import get_mlflow_config
from kedro_mlflow.framework.hooks.utils import _assert_mlflow_enabled, _flatten_dict


class MlflowNodeHook:
    def __init__(self):
        self.flatten = False
        self.recursive = True
        self.sep = "."
        self.long_parameters_strategy = "fail"
        self._is_mlflow_enabled = True

    @property
    def _logger(self) -> logging.Logger:
        return logging.getLogger(__name__)

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
        self._is_mlflow_enabled = _assert_mlflow_enabled(run_params["pipeline_name"])

        if self._is_mlflow_enabled:
            mlflow_config = get_mlflow_config()

            self.flatten = mlflow_config.tracking.params.dict_params.flatten
            self.recursive = mlflow_config.tracking.params.dict_params.recursive
            self.sep = mlflow_config.tracking.params.dict_params.sep
            self.long_params_strategy = (
                mlflow_config.tracking.params.long_params_strategy
            )

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
        This hook logs all the parameters of the nodes in mlflow.
        Args:
            node: The ``Node`` to run.
            catalog: A ``DataCatalog`` containing the node's inputs and outputs.
            inputs: The dictionary of inputs dataset.
            is_async: Whether the node was run in ``async`` mode.
            run_id: The id of the run.
        """

        # only parameters will be logged. Artifacts must be declared manually in the catalog
        if self._is_mlflow_enabled:
            params_inputs = {}
            for k, v in inputs.items():
                # detect parameters automatically based on kedro reserved names
                if k.startswith("params:"):
                    params_inputs[k[7:]] = v
                elif k == "parameters":
                    params_inputs[k] = v

            # dictionary parameters may be flattened for readibility
            if self.flatten:
                params_inputs = _flatten_dict(
                    d=params_inputs, recursive=self.recursive, sep=self.sep
                )

            # logging parameters based on defined strategy
            for k, v in params_inputs.items():
                self.log_param(k, v)

    def log_param(self, name: str, value: Union[Dict, int, bool, str]) -> None:
        str_value = str(value)
        str_value_length = len(str_value)
        if str_value_length <= MAX_PARAM_VAL_LENGTH:
            return mlflow.log_param(name, value)
        else:
            if self.long_params_strategy == "fail":
                raise ValueError(
                    f"Parameter '{name}' length is {str_value_length}, "
                    f"while mlflow forces it to be lower than '{MAX_PARAM_VAL_LENGTH}'. "
                    "If you want to bypass it, try to change 'long_params_strategy' to"
                    " 'tag' or 'truncate' in the 'mlflow.yml'configuration file."
                )
            elif self.long_params_strategy == "tag":
                self._logger.warning(
                    f"Parameter '{name}' (value length {str_value_length}) is set as a tag."
                )
                mlflow.set_tag(name, value)
            elif self.long_params_strategy == "truncate":
                self._logger.warning(
                    f"Parameter '{name}' (value length {str_value_length}) is truncated to its {MAX_PARAM_VAL_LENGTH} first characters."
                )
                mlflow.log_param(name, str_value[0:MAX_PARAM_VAL_LENGTH])


# this hooks instaitation is necessary for auto-registration
mlflow_node_hook = MlflowNodeHook()
