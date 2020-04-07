import mlflow
import re
from typing import Any, Dict

from kedro.hooks import hook_impl
from kedro.io import DataCatalog
from kedro.pipeline import Pipeline
from kedro.pipeline.node import Node
from kedro.versioning.journal import _git_sha

from kedro_mlflow.context import get_mlflow_conf
from kedro_mlflow.utils import generate_kedro_command

class MlflowPipelineSpecs:

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
        mlflow_conf = get_mlflow_conf(project_path=run_params["project_path"],
                                                  env=run_params["env"])

        # TODO : if the pipeline fails, we need to be able to end stop the mlflow run
        # cannot figure out how to do this within hooks
        run_name = mlflow_conf.run_opts["name"]  \
            if mlflow_conf.run_opts["name"] is not None \
            else run_params["pipeline_name"]
        mlflow.start_run(run_id=mlflow_conf.run_opts["id"],
                         experiment_id=mlflow_conf.experiment.experiment_id,
                         run_name=run_name,
                         nested=mlflow_conf.run_opts["nested"])
        mlflow.set_tags(run_params)
        # add manually git sha for consistency with the journal
        # TODO : this does not take into account not committed files, so it 
        # does not ensure reproducibility. Define what to do.
        mlflow.set_tag("git_sha", _git_sha(run_params["project_path"]))
        mlflow.set_tag("kedro_command", generate_kedro_command(tags=run_params["tags"], 
                                                               node_names=run_params["node_names"],
                                                               from_nodes=run_params["from_nodes"],
                                                               to_nodes=run_params["to_nodes"],
                                                               from_inputs=run_params["from_inputs"],
                                                               load_versions=run_params["load_versions"], 
                                                               pipeline_name=run_params["pipeline_name"]))


    @hook_impl
    def after_pipeline_run(
        self, run_params: Dict[str, Any], pipeline: Pipeline, catalog: DataCatalog,
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

        #Close the mlflow active run at the end of the pipeline to avoid interactions with further
        mlflow.end_run()
