from kedro_mlflow.framework.context.mlflow_context import get_mlflow_config


def _assert_mlflow_enabled(pipeline_name: str) -> bool:

    mlflow_config = get_mlflow_config()
    # TODO: we may want to enable to filter on tags
    # but we need to deal with the case when several tags are passed
    # what to do if 1 out of 2 is in the list?
    disabled_pipelines = mlflow_config.disable_tracking_opts.get("pipelines") or []
    if pipeline_name in disabled_pipelines:
        return False

    return True
