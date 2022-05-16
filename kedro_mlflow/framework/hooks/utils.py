from typing import Dict

from kedro_mlflow.config.kedro_mlflow_config import KedroMlflowConfig


def _assert_mlflow_enabled(
    pipeline_name: str, mlflow_config: KedroMlflowConfig
) -> bool:

    # TODO: we may want to enable to filter on tags
    # but we need to deal with the case when several tags are passed
    # what to do if 1 out of 2 is in the list?
    disabled_pipelines = mlflow_config.tracking.disable_tracking.pipelines
    if pipeline_name in disabled_pipelines:
        return False

    return True


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
