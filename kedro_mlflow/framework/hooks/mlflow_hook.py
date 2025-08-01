import os
import re
from logging import Logger, getLogger
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Union

import mlflow
from kedro.config import MissingConfigException
from kedro.framework.context import KedroContext
from kedro.framework.hooks import hook_impl
from kedro.framework.startup import _get_project_metadata
from kedro.io import CatalogProtocol, DataCatalog
from kedro.pipeline import Pipeline
from kedro.pipeline.node import Node
from mlflow.entities import RunStatus
from mlflow.models import infer_signature
from mlflow.tracking import MlflowClient
from mlflow.utils.validation import MAX_PARAM_VAL_LENGTH
from omegaconf import OmegaConf
from pydantic import __version__ as pydantic_version

from kedro_mlflow.config.kedro_mlflow_config import KedroMlflowConfig
from kedro_mlflow.config.resolvers import resolve_random_name
from kedro_mlflow.framework.hooks.utils import (
    _assert_mlflow_enabled,
    _flatten_dict,
    _generate_kedro_command,
)
from kedro_mlflow.io.catalog.switch_catalog_logging import switch_catalog_logging
from kedro_mlflow.io.metrics import (
    MlflowMetricDataset,
    MlflowMetricHistoryDataset,
    MlflowMetricsHistoryDataset,
)
from kedro_mlflow.mlflow import KedroPipelineModel
from kedro_mlflow.pipeline.pipeline_ml import PipelineML


class MlflowHook:
    def __init__(self):
        self._is_mlflow_enabled = True
        self.flatten = False
        self.recursive = True
        self.sep = "."
        self.long_parameters_strategy = "fail"
        self.run_id = None  # we store the run_id because the hook is stateful and we need to keep track of the active run between the different threads

    @property
    def _logger(self) -> Logger:
        return getLogger(__name__)

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

        self._logger.info(r"Registering new custom resolver: 'km.random_name'")
        if not OmegaConf.has_resolver("km.random_name"):
            OmegaConf.register_new_resolver(
                "km.random_name", resolve_random_name, use_cache=True
            )

        try:
            if "mlflow" not in context.config_loader.config_patterns.keys():
                context.config_loader.config_patterns.update(
                    {"mlflow": ["mlflow*", "mlflow*/**", "**/mlflow*"]}
                )
            conf_mlflow_yml = context.config_loader["mlflow"]
        except MissingConfigException:
            self._logger.warning(
                "No 'mlflow.yml' config file found in environment. Default configuration will be used. Use ``kedro mlflow init`` command in CLI to customize the configuration."
            )
            # we create an empty dict to have the same behaviour when the mlflow.yml
            # is commented out. In this situation there is no MissingConfigException
            # but we got an empty dict
            conf_mlflow_yml = {}

        mlflow_config = (
            KedroMlflowConfig.model_validate({**conf_mlflow_yml})
            if pydantic_version > "2.0.0"
            else KedroMlflowConfig.parse_obj({**conf_mlflow_yml})
        )

        self._already_active_mlflow = False
        if mlflow.active_run():
            self._already_active_mlflow = True
            active_run_info = mlflow.active_run().info

            self._logger.warning(
                f"The mlflow run {active_run_info.run_id} is already active. Configuration is inferred from the environment, and mlflow.yml is ignored."
            )

            mlflow_config.server.mlflow_tracking_uri = mlflow.get_tracking_uri()
            mlflow_config.server._mlflow_client = MlflowClient(
                tracking_uri=mlflow_config.server.mlflow_tracking_uri
            )
            self._logger.warning(f"{mlflow_config.server.mlflow_tracking_uri=}")

            mlflow_config.tracking.run.id = active_run_info.run_id
            self._logger.warning(f"{mlflow_config.tracking.run.id=}")

            mlflow_config.tracking.experiment.name = mlflow.get_experiment(
                experiment_id=active_run_info.experiment_id
            ).name
            self._logger.warning(f"{mlflow_config.tracking.experiment.name=}")

        else:
            # we infer and setup the configuration only if there is no active run:
            # if there is an active run, we assume everything is already configured and
            # configuration was inferred from environment so there is no need to set it up
            # the goal is to enable an orchestrator to start the run by itself
            if (
                conf_mlflow_yml.get("tracking", {}).get("experiment", {}).get("name")
                is None
            ):
                # the only default which is changed
                # is to use the package_name as the experiment name
                experiment_name = context._package_name
                if experiment_name is None:
                    # context._package_name may be None if the session is created interactively
                    metadata = _get_project_metadata(context.project_path)
                    experiment_name = metadata.package_name
                mlflow_config.tracking.experiment.name = experiment_name

            mlflow_config.setup(
                context
            )  # setup global mlflow configuration (environment variables, tracking uri, experiment...)

        # store in context for interactive use
        # we use __setattr__ instead of context.mlflow because
        # the class will become frozen in kedro>=0.19
        context.__setattr__("mlflow", mlflow_config)

        self.mlflow_config = mlflow_config  # store for further reuse

    @hook_impl
    def after_catalog_created(  # noqa: PLR0913
        self,
        catalog: CatalogProtocol,
        conf_catalog: dict[str, Any],
        conf_creds: dict[str, Any],
        parameters: dict[str, Any],
        save_version: str,
        load_versions: dict[str, str],
    ) -> None:
        # we use this hooks to modif "MlflowmetricsDataset" to ensure consistency
        # of the metric name with the catalog name
        for name, dataset in catalog.items():
            if (
                isinstance(dataset, MlflowMetricsHistoryDataset)
                and dataset._prefix is None
            ):
                if dataset._run_id is not None:
                    catalog[name] = MlflowMetricsHistoryDataset(
                        run_id=dataset._run_id, prefix=name
                    )
                else:
                    catalog[name] = MlflowMetricsHistoryDataset(prefix=name)

            if isinstance(dataset, MlflowMetricDataset) and dataset.key is None:
                if dataset._run_id is not None:
                    catalog[name] = MlflowMetricDataset(
                        run_id=dataset._run_id,
                        key=name,
                        load_args=dataset._load_args,
                        save_args=dataset._save_args,
                    )
                else:
                    catalog[name] = MlflowMetricDataset(
                        key=name,
                        load_args=dataset._load_args,
                        save_args=dataset._save_args,
                    )

            if isinstance(dataset, MlflowMetricHistoryDataset) and dataset.key is None:
                if dataset._run_id is not None:
                    catalog[name] = MlflowMetricHistoryDataset(
                        run_id=dataset._run_id,
                        key=name,
                        load_args=dataset._load_args,
                        save_args=dataset._save_args,
                    )
                else:
                    catalog[name] = MlflowMetricHistoryDataset(
                        key=name,
                        load_args=dataset._load_args,
                        save_args=dataset._save_args,
                    )

    @hook_impl
    def before_pipeline_run(
        self, run_params: dict[str, Any], pipeline: Pipeline, catalog: DataCatalog
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
                    "tags": Optional[list[str]],
                    "from_nodes": Optional[list[str]],
                    "to_nodes": Optional[list[str]],
                    "node_names": Optional[list[str]],
                    "from_inputs": Optional[list[str]],
                    "load_versions": Optional[list[str]],
                    "pipeline_name": str,
                    "extra_params": Optional[dict[str, Any]],
                }
            pipeline: The ``Pipeline`` that will be run.
            catalog: The ``DataCatalog`` to be used during the run.
        """
        self._is_mlflow_enabled = _assert_mlflow_enabled(
            run_params["pipeline_name"], self.mlflow_config
        )

        if self._is_mlflow_enabled:
            # params for further for node logging
            self.flatten = self.mlflow_config.tracking.params.dict_params.flatten
            self.recursive = self.mlflow_config.tracking.params.dict_params.recursive
            self.sep = self.mlflow_config.tracking.params.dict_params.sep
            self.long_params_strategy = (
                self.mlflow_config.tracking.params.long_params_strategy
            )

            run_name = (
                self.mlflow_config.tracking.run.name
                or run_params["pipeline_name"]
                or "__default__"
            )

            if self._already_active_mlflow:
                self.run_id = mlflow.active_run().info.run_id
                self._logger.warning(
                    f"A mlflow run was already active (run_id='{self.run_id}') before the KedroSession was started. This run will be used for logging."
                )
            else:
                mlflow.start_run(
                    run_id=self.mlflow_config.tracking.run.id,
                    experiment_id=self.mlflow_config.tracking.experiment._experiment.experiment_id,
                    run_name=run_name,
                    nested=self.mlflow_config.tracking.run.nested,
                )
                self.run_id = mlflow.active_run().info.run_id
                self._logger.info(
                    f"Mlflow run '{mlflow.active_run().info.run_name}' - '{self.run_id}' has started"
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
            self._logger.info(
                "kedro-mlflow logging is deactivated for this pipeline in the configuration. This includes DataSets and parameters."
            )
            switch_catalog_logging(catalog, False)

    @hook_impl
    def before_node_run(
        self, node: Node, catalog: DataCatalog, inputs: dict[str, Any], is_async: bool
    ) -> None:
        """Hook to be invoked before a node runs.
        This hook logs all the parameters of the nodes in mlflow.
        Args:
            node: The ``Node`` to run.
            catalog: A ``DataCatalog`` containing the node's inputs and outputs.
            inputs: The dictionary of inputs dataset.
            is_async: Whether the node was run in ``async`` mode.
        """
        if self.run_id is not None:
            # Reopening the run ensures the run_id started at the beginning of the pipeline
            # is used for all tracking. This is necessary because to bypass mlflow thread safety
            # each call to the "active run" now creates a new run when started in a new thread. See
            # https://github.com/Galileo-Galilei/kedro-mlflow/issues/613
            # https://github.com/Galileo-Galilei/kedro-mlflow/pull/615
            # https://github.com/Galileo-Galilei/kedro-mlflow/issues/623
            # https://github.com/Galileo-Galilei/kedro-mlflow/issues/624

            # If self.run_id is None, this means that the no run was ever started, i.e. that we have deactivated mlflow for this pipeline
            try:
                mlflow.start_run(
                    run_id=self.run_id,
                    nested=self.mlflow_config.tracking.run.nested,
                )
                self._logger.debug(
                    f"Restarting mlflow run '{mlflow.active_run().info.run_name}' - '{self.run_id}' at node level for multi-threading"
                )
            except Exception as err:  # pragma: no cover
                if f"Run with UUID {self.run_id} is already active" in str(err):
                    # This means that the run was started before in the same thread, likely at the beginning of another node
                    pass
                else:
                    raise err

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

            # sanitize params inputs to avoid mlflow errors
            params_inputs = {
                self.sanitize_param_name(k): v for k, v in params_inputs.items()
            }

            # logging parameters based on defined strategy
            for k, v in params_inputs.items():
                self._log_param(k, v)

    def _log_param(self, name: str, value: Union[dict, int, bool, str]) -> None:
        str_value = str(value)
        str_value_length = len(str_value)
        if str_value_length <= MAX_PARAM_VAL_LENGTH:
            return mlflow.log_param(name, value)
        elif self.long_params_strategy == "fail":
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
        run_params: dict[str, Any],
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
                    "tags": Optional[list[str]],
                    "from_nodes": Optional[list[str]],
                    "to_nodes": Optional[list[str]],
                    "node_names": Optional[list[str]],
                    "from_inputs": Optional[list[str]],
                    "load_versions": Optional[list[str]],
                    "pipeline_name": str,
                    "extra_params": Optional[dict[str, Any]],
                }
            pipeline: The ``Pipeline`` that was run.
            catalog: The ``DataCatalog`` used during the run.
        """
        if self._is_mlflow_enabled:
            if isinstance(pipeline, PipelineML):
                # Materialize dataset factories
                for dataset in pipeline.datasets():
                    catalog.exists(dataset)

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

                            # all pipeline params will be overridable at predict time: https://mlflow.org/docs/latest/model/signatures.html#model-signatures-with-inference-params
                            # I add the special "runner" parameter to be able to choose it at runtime
                            pipeline_params = {
                                ds_name[7:]: catalog.load(ds_name)
                                for ds_name in pipeline.inference.inputs()
                                if ds_name.startswith("params:")
                            } | {"runner": "SequentialRunner"}
                            model_signature = infer_signature(
                                model_input=input_data,
                                params=pipeline_params,
                            )

                    mlflow.pyfunc.log_model(
                        python_model=kedro_pipeline_model,
                        artifacts=artifacts,
                        signature=model_signature,
                        **log_model_kwargs,
                    )
            # Close the mlflow active run at the end of the pipeline to avoid interactions with further runs
            if self._already_active_mlflow:
                self._logger.warning(
                    f"The run '{mlflow.active_run().info.run_id}' was already opened before launching 'kedro run' so it is not closed. You should close it manually."
                )
            else:
                mlflow.end_run()

        else:
            switch_catalog_logging(catalog, True)

    @hook_impl
    def on_pipeline_error(
        self,
        error: Exception,
        run_params: dict[str, Any],
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
                     "tags": Optional[list[str]],
                     "from_nodes": Optional[list[str]],
                     "to_nodes": Optional[list[str]],
                     "node_names": Optional[list[str]],
                     "from_inputs": Optional[list[str]],
                     "load_versions": Optional[list[str]],
                     "pipeline_name": str,
                     "extra_params": Optional[dict[str, Any]]
                   }
            pipeline: (Not used) The ``Pipeline`` that will was run.
            catalog: (Not used) The ``DataCatalog`` used during the run.
        """
        if self._is_mlflow_enabled:
            if self._already_active_mlflow:
                self._logger.warning(
                    f"The run '{mlflow.active_run().info.run_id}' was already opened before launching 'kedro run' so it is not closed. You should close it manually."
                )
            else:
                # first, close all runs within the thread
                while mlflow.active_run():
                    current_run_id = mlflow.active_run().info.run_id
                    self._logger.info(
                        f"The run '{current_run_id}' was closed because of an error in the pipeline."
                    )
                    mlflow.end_run(RunStatus.to_string(RunStatus.FAILED))
                    pipeline_run_id_is_closed = current_run_id == self.run_id

                # second, ensure that parent run in another thread is closed
                if not pipeline_run_id_is_closed:
                    self.mlflow_config.server._mlflow_client.set_terminated(
                        self.run_id, RunStatus.to_string(RunStatus.FAILED)
                    )
                    self._logger.info(
                        f"The parent run '{self.run_id}' was closed because of an error in the pipeline."
                    )

        else:  # pragma: no cover
            # the catalog is supposed to be reloaded each time with _get_catalog,
            # hence it should not be modified. this is only a safeguard
            switch_catalog_logging(catalog, True)

    def sanitize_param_name(self, name: str) -> str:
        # regex taken from MLFlow codebase: https://github.com/mlflow/mlflow/blob/e40e782b6fcab473159e6d4fee85bc0fc10f78fd/mlflow/utils/validation.py#L140C1-L148C44

        # for windows colon ':' are not accepted
        matching_pattern = r"^[/\w.\- ]*$" if is_windows() else r"^[/\w.\- :]*$"

        if re.match(matching_pattern, name):
            return name
        else:
            replacement_pattern = r"[^/\w.\- ]" if is_windows() else r"[^/\w.\- :]"
            # Replace invalid characters with underscore
            sanitized_name = re.sub(replacement_pattern, "_", name)
            self._logger.warning(
                f"'{name}' is not a valid name for a mlflow paramter. It is renamed as '{sanitized_name}'"
            )
            return sanitized_name


def is_windows():
    return os.name == "nt"


mlflow_hook = MlflowHook()
