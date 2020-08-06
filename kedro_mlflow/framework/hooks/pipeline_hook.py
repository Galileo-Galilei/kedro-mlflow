import sys
from pathlib import Path
from typing import Any, Dict, Union

import mlflow
import yaml
from kedro.framework.hooks import hook_impl
from kedro.io import DataCatalog
from kedro.pipeline import Pipeline
from kedro.versioning.journal import _git_sha

from kedro_mlflow.framework.context import get_mlflow_config
from kedro_mlflow.mlflow import KedroPipelineModel
from kedro_mlflow.pipeline.pipeline_ml import PipelineML
from kedro_mlflow.utils import _parse_requirements


class MlflowPipelineHook:
    def __init__(
        self,
        conda_env: Union[str, Path, Dict[str, Any]] = None,
        model_name: Union[str, None] = "model",
    ):
        self.conda_env = _format_conda_env(conda_env)
        self.model_name = model_name

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
        mlflow_conf = get_mlflow_config(
            project_path=run_params["project_path"], env=run_params["env"]
        )
        mlflow.set_tracking_uri(mlflow_conf.mlflow_tracking_uri)
        # TODO : if the pipeline fails, we need to be able to end stop the mlflow run
        # cannot figure out how to do this within hooks
        run_name = (
            mlflow_conf.run_opts["name"]
            if mlflow_conf.run_opts["name"] is not None
            else run_params["pipeline_name"]
        )
        mlflow.start_run(
            run_id=mlflow_conf.run_opts["id"],
            experiment_id=mlflow_conf.experiment.experiment_id,
            run_name=run_name,
            nested=mlflow_conf.run_opts["nested"],
        )
        mlflow.set_tags(run_params)
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

        if isinstance(pipeline, PipelineML):
            pipeline_catalog = pipeline.extract_pipeline_catalog(catalog)
            artifacts = pipeline.extract_pipeline_artifacts(pipeline_catalog)
            mlflow.pyfunc.log_model(
                artifact_path=self.model_name,
                python_model=KedroPipelineModel(
                    pipeline_ml=pipeline, catalog=pipeline_catalog
                ),
                artifacts=artifacts,
                conda_env=self.conda_env,
            )
        # Close the mlflow active run at the end of the pipeline to avoid interactions with further runs
        mlflow.end_run()


def _generate_kedro_command(
    tags, node_names, from_nodes, to_nodes, from_inputs, load_versions, pipeline_name
):
    cmd_list = ["kedro", "run"]
    SEP = "="
    if len(from_inputs) > 0:
        cmd_list.append("--from-inputs" + SEP + ",".join(from_inputs))
    if len(from_nodes) > 0:
        cmd_list.append("--from-nodes" + SEP + ",".join(from_nodes))
    if len(to_nodes) > 0:
        cmd_list.append("--to-nodes" + SEP + ",".join(to_nodes))
    if len(node_names) > 0:
        cmd_list.append("--node" + SEP + ",".join(node_names))
    if pipeline_name:
        cmd_list.append("--pipeline" + SEP + pipeline_name)
    if len(tags) > 0:
        # "tag" is the name of the command, "tags" the value in run_params
        cmd_list.append("--tag" + SEP + ",".join(tags))
    if len(load_versions) > 0:
        # "load_version" is the name of the command, "load_versions" the value in run_params
        formatted_versions = [f"{k}:{v}" for k, v in load_versions.items()]
        cmd_list.append("--load-version" + SEP + ",".join(formatted_versions))

    kedro_cmd = " ".join(cmd_list)
    return kedro_cmd


def _format_conda_env(
    conda_env: Union[str, Path, Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Best effort to get dependecies of the project.

    Keyword Arguments:
        conda_env {[type]} -- It can be either :
            - a path to a "requirements.txt": In this case
            the packages are parsed and a conda env with
            your current python_version and these dependencies is returned
            - a path to an "environment.yml" : data is loaded and used as they are
            - a Dict : used as the environment
            - None (default: {None})

    Returns:
        Dict[str, Any] -- [description]
    """
    python_version = ".".join(
        [
            str(sys.version_info.major),
            str(sys.version_info.minor),
            str(sys.version_info.micro),
        ]
    )
    if isinstance(conda_env, str):
        conda_env = Path(conda_env)

    if isinstance(conda_env, Path):
        if conda_env.suffix in (".yml", ".yaml"):
            with open(conda_env, mode="r") as file_handler:
                conda_env = yaml.safe_load(file_handler)
        elif conda_env.suffix in (".txt"):
            conda_env = {
                "python": python_version,
                "dependencies": _parse_requirements(conda_env),
            }
    elif conda_env is None:
        conda_env = {"python": python_version}
    elif isinstance(conda_env, dict):
        return conda_env
    else:
        raise ValueError(
            """Invalid conda_env. It can be either :
            - a Dict : used as the environment without control
            - None (default: {None}) : Only the python vresion will be stored.
            - a path to a "requirements.txt": In this case
            the packages are parsed and a conda env with
            your current python_version and these dependencies is returned
            - a path to an "environment.yml" : data is loaded and used as they are
            """
        )

    return conda_env
