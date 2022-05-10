import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, Union

import mlflow
from kedro.framework.context import KedroContext
from kedro.framework.hooks import hook_impl
from kedro.io import DataCatalog
from kedro.pipeline import Pipeline
from kedro.pipeline.node import Node
from mlflow.entities import RunStatus
from mlflow.models import infer_signature
from mlflow.utils.validation import MAX_PARAM_VAL_LENGTH

from kedro_mlflow.config.kedro_mlflow_config import (
    KedroMlflowConfig,
    _get_mlflow_config,
)
from kedro_mlflow.io.metrics import (
    MlflowMetricDataSet,
    MlflowMetricHistoryDataSet,
    MlflowMetricsDataSet,
)
from kedro_mlflow.mlflow import KedroPipelineModel
from kedro_mlflow.pipeline.pipeline_ml import PipelineML


class KedroMlflowHook:
    def __init__(self):
        self._is_mlflow_enabled = True
        self.flatten = False
        self.recursive = True
        self.sep = "."
        self.long_parameters_strategy = "fail"

    @property
    def _logger(self) -> logging.Logger:
        return logging.getLogger(__name__)

    @hook_impl
    def after_context_created(
        self,
        context: KedroContext,
    ) -> None:
        """Hooks to be invoked after a `KedroContext` is created. This is the earliest
        hook triggered within a Kedro run. The `KedroContext` stores useful information
        such as `credentials`, `config_loader` and `env`.
        Args:
            context: The context that was created.
        """

        mlflow_config = _get_mlflow_config(context=context)
        mlflow_config.setup(context=context)

        # dynamically modify context for interactive use
        context.mlflow_config = mlflow_config

        # store in class for further reuse in other hooks
        self.mlflow_config = mlflow_config

    @hook_impl
    def after_catalog_created(
        self,
        catalog: DataCatalog,
        conf_catalog: Dict[str, Any],
        conf_creds: Dict[str, Any],
        feed_dict: Dict[str, Any],
        save_version: str,
        load_versions: str,
    ):

        for name, dataset in catalog._data_sets.items():

            if isinstance(dataset, MlflowMetricsDataSet) and dataset._prefix is None:
                if dataset._run_id is not None:
                    catalog._data_sets[name] = MlflowMetricsDataSet(
                        run_id=dataset._run_id, prefix=name
                    )
                else:
                    catalog._data_sets[name] = MlflowMetricsDataSet(prefix=name)

            if isinstance(dataset, MlflowMetricDataSet) and dataset.key is None:
                if dataset._run_id is not None:
                    catalog._data_sets[name] = MlflowMetricDataSet(
                        run_id=dataset._run_id,
                        key=name,
                        load_args=dataset._load_args,
                        save_args=dataset._save_args,
                    )
                else:
                    catalog._data_sets[name] = MlflowMetricDataSet(
                        key=name,
                        load_args=dataset._load_args,
                        save_args=dataset._save_args,
                    )

            if isinstance(dataset, MlflowMetricHistoryDataSet) and dataset.key is None:
                if dataset._run_id is not None:
                    catalog._data_sets[name] = MlflowMetricHistoryDataSet(
                        run_id=dataset._run_id,
                        key=name,
                        load_args=dataset._load_args,
                        save_args=dataset._save_args,
                    )
                else:
                    catalog._data_sets[name] = MlflowMetricHistoryDataSet(
                        key=name,
                        load_args=dataset._load_args,
                        save_args=dataset._save_args,
                    )

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
        self._is_mlflow_enabled = _assert_mlflow_enabled(
            self.mlflow_config, run_params["pipeline_name"]
        )

        if self._is_mlflow_enabled:

            self.flatten = self.mlflow_config.tracking.params.dict_params.flatten
            self.recursive = self.mlflow_config.tracking.params.dict_params.recursive
            self.sep = self.mlflow_config.tracking.params.dict_params.sep
            self.long_params_strategy = (
                self.mlflow_config.tracking.params.long_params_strategy
            )
            run_name = (
                self.mlflow_config.tracking.run.name or run_params["pipeline_name"]
            )

            mlflow.start_run(
                run_id=self.mlflow_config.tracking.run.id,
                experiment_id=self.mlflow_config.tracking.experiment._experiment.experiment_id,
                run_name=run_name,
                nested=self.mlflow_config.tracking.run.nested,
            )
            # Set tags only for run parameters that have values.
            mlflow.set_tags({k: v for k, v in run_params.items() if v})
            # add manually git sha for consistency with the journal
            # TODO : this does not take into account not committed files, so it
            # does not ensure reproducibility. Define what to do.

            mlflow.set_tag(
                "kedro_command",
                _generate_kedro_command(
                    tags=run_params["tags"],
                    node_names=run_params["node_names"],
                    from_nodes=run_params["from_nodes"],
                    to_nodes=run_params["to_nodes"],
                    from_inputs=run_params["from_inputs"],
                    load_versions=run_params["load_versions"],
                    pipeline_name=run_params["pipeline_name"],
                ),
            )
        else:
            logging.info(
                "kedro-mlflow logging is deactivated for this pipeline in the configuration. This includes DataSets and parameters."
            )
            _switch_catalog_logging(catalog, False)

    @hook_impl
    def before_node_run(
        self, node: Node, catalog: DataCatalog, inputs: Dict[str, Any], is_async: bool
    ) -> None:
        """Hook to be invoked before a node runs.
        This hook logs all the parameters of the nodes in mlflow.
        Args:
            node: The ``Node`` to run.
            catalog: A ``DataCatalog`` containing the node's inputs and outputs.
            inputs: The dictionary of inputs dataset.
            is_async: Whether the node was run in ``async`` mode.
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
                self._log_param(k, v)

    def _log_param(self, name: str, value: Union[Dict, int, bool, str]) -> None:
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

    @hook_impl
    def after_pipeline_run(
        self,
        run_params: Dict[str, Any],
        pipeline: Pipeline,
        catalog: DataCatalog,
    ) -> None:
        """Hook to be invoked after a pipeline runs.
        Args:
            run_params: The params needed for the given run.
                Should be identical to the data logged by Journal.
                # @fixme: this needs to be modelled explicitly as code, instead of comment
                Schema: {
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
            pipeline: The ``Pipeline`` that was run.
            catalog: The ``DataCatalog`` used during the run.
        """
        if self._is_mlflow_enabled:
            if isinstance(pipeline, PipelineML):
                with TemporaryDirectory() as tmp_dir:
                    # This will be removed at the end of the context manager,
                    # but we need to log in mlflow before moving the folder
                    kedro_pipeline_model = KedroPipelineModel(
                        pipeline=pipeline.inference,
                        catalog=catalog,
                        input_name=pipeline.input_name,
                        **pipeline.kpm_kwargs,
                    )
                    artifacts = kedro_pipeline_model.extract_pipeline_artifacts(
                        parameters_saving_folder=Path(tmp_dir)
                    )

                    log_model_kwargs = pipeline.log_model_kwargs.copy()
                    model_signature = log_model_kwargs.pop("signature", None)
                    if isinstance(model_signature, str):
                        if model_signature == "auto":
                            input_data = catalog.load(pipeline.input_name)
                            model_signature = infer_signature(model_input=input_data)

                    mlflow.pyfunc.log_model(
                        python_model=kedro_pipeline_model,
                        artifacts=artifacts,
                        signature=model_signature,
                        **log_model_kwargs,
                    )
            # Close the mlflow active run at the end of the pipeline to avoid interactions with further runs
            mlflow.end_run()
        else:
            _switch_catalog_logging(catalog, True)

        @hook_impl
        def on_pipeline_error(
            self,
            error: Exception,
            run_params: Dict[str, Any],
            pipeline: Pipeline,
            catalog: DataCatalog,
        ):
            """Hook invoked when the pipeline execution fails.
                All the mlflow runs must be closed to avoid interference with further execution.

            Args:
                error: (Not used) The uncaught exception thrown during the pipeline run.
                run_params: (Not used) The params used to run the pipeline.
                    Should be identical to the data logged by Journal with the following schema::

                        {
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
                            "extra_params": Optional[Dict[str, Any]]
                        }
                pipeline: (Not used) The ``Pipeline`` that will was run.
                catalog: (Not used) The ``DataCatalog`` used during the run.
            """
            if self._is_mlflow_enabled:
                while mlflow.active_run():
                    mlflow.end_run(RunStatus.to_string(RunStatus.FAILED))
            else:  # pragma: no cover
                # the catalog is supposed to be reloaded each time with _get_catalog,
                # hence it should not be modified. this is only a safeguard
                _switch_catalog_logging(catalog, True)


def _generate_kedro_command(
    tags, node_names, from_nodes, to_nodes, from_inputs, load_versions, pipeline_name
):
    cmd_list = ["kedro", "run"]
    SEP = "="
    if from_inputs:
        cmd_list.append("--from-inputs" + SEP + ",".join(from_inputs))
    if from_nodes:
        cmd_list.append("--from-nodes" + SEP + ",".join(from_nodes))
    if to_nodes:
        cmd_list.append("--to-nodes" + SEP + ",".join(to_nodes))
    if node_names:
        cmd_list.append("--node" + SEP + ",".join(node_names))
    if pipeline_name:
        cmd_list.append("--pipeline" + SEP + pipeline_name)
    if tags:
        # "tag" is the name of the command, "tags" the value in run_params
        cmd_list.append("--tag" + SEP + ",".join(tags))
    if load_versions:
        # "load_version" is the name of the command, "load_versions" the value in run_params
        formatted_versions = [f"{k}:{v}" for k, v in load_versions.items()]
        cmd_list.append("--load-version" + SEP + ",".join(formatted_versions))

    kedro_cmd = " ".join(cmd_list)
    return kedro_cmd


def _assert_mlflow_enabled(
    mlflow_config: KedroMlflowConfig, pipeline_name: str
) -> bool:

    # TODO: we may want to enable to filter on tags
    # but we need to deal with the case when several tags are passed
    # what to do if 1 out of 2 is in the list?
    disabled_pipelines = mlflow_config.tracking.disable_tracking.pipelines
    if pipeline_name in disabled_pipelines:
        return False

    return True


def _flatten_dict(d: Dict, recursive: bool = True, sep: str = ".") -> Dict:
    def expand(key, value):
        if isinstance(value, dict):
            new_value = (
                _flatten_dict(value, recursive=recursive, sep=sep)
                if recursive
                else value
            )
            return [(f"{key}{sep}{k}", v) for k, v in new_value.items()]
        else:
            return [(f"{key}", value)]

    items = [item for k, v in d.items() for item in expand(k, v)]

    return dict(items)


def _switch_catalog_logging(catalog, logging_flag=True):
    for name, data_set in catalog._data_sets.items():
        if type(data_set).__name__.startswith("Mlflow"):
            catalog._data_sets[name]._logging_activated = logging_flag


# this hooks instantiation is necessary for auto-registration
kedro_mlflow_hook = KedroMlflowHook()
