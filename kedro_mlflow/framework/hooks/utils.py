from typing import Dict

from kedro_mlflow.config.kedro_mlflow_config import get_mlflow_config


def _assert_mlflow_enabled(pipeline_name: str) -> bool:

    mlflow_config = get_mlflow_config()
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
