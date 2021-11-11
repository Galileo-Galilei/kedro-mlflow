import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict

import mlflow
from kedro.framework.hooks import hook_impl
from kedro.io import DataCatalog
from kedro.pipeline import Pipeline
from kedro.versioning.journal import _git_sha
from mlflow.entities import RunStatus
from mlflow.models import infer_signature

from kedro_mlflow.config import get_mlflow_config
from kedro_mlflow.framework.hooks.utils import _assert_mlflow_enabled
from kedro_mlflow.io.catalog.switch_catalog_logging import switch_catalog_logging
from kedro_mlflow.io.metrics import (
    MlflowMetricDataSet,
    MlflowMetricHistoryDataSet,
    MlflowMetricsDataSet,
)
from kedro_mlflow.mlflow import KedroPipelineModel
from kedro_mlflow.pipeline.pipeline_ml import PipelineML


class MlflowPipelineHook:
    def __init__(self):
        self._is_mlflow_enabled = True

    @hook_impl
    def after_catalog_created(
        self,
        catalog: DataCatalog,
        conf_catalog: Dict[str, Any],
        conf_creds: Dict[str, Any],
        feed_dict: Dict[str, Any],
        save_version: str,
        load_versions: str,
        run_id: str,
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
            mlflow_config.setup()

            run_name = mlflow_config.tracking.run.name or run_params["pipeline_name"]

            mlflow.start_run(
                run_id=mlflow_config.tracking.run.id,
                experiment_id=mlflow_config.tracking.experiment._experiment.experiment_id,
                run_name=run_name,
                nested=mlflow_config.tracking.run.nested,
            )
            # Set tags only for run parameters that have values.
            mlflow.set_tags({k: v for k, v in run_params.items() if v})
            # add manually git sha for consistency with the journal
            # TODO : this does not take into account not committed files, so it
            # does not ensure reproducibility. Define what to do.
            mlflow.set_tag("git_sha", _git_sha(run_params["project_path"]))
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
            switch_catalog_logging(catalog, False)

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
            switch_catalog_logging(catalog, True)

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
                     "run_id": str
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
            switch_catalog_logging(catalog, True)


mlflow_pipeline_hook = MlflowPipelineHook()


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
