import logging.config

from IPython import get_ipython
from kedro.framework.startup import bootstrap_project
from mlflow.tracking import MlflowClient


def reload_kedro_mlflow(line=None, local_ns=None):
    metadata = bootstrap_project(
        local_ns["project_path"]
    )  # project_path is a global variable defined by init_kedro

    mlflow_client = MlflowClient(
        tracking_uri=local_ns["context"].mlflow.server.mlflow_tracking_uri
    )
    global_variables = {"mlflow_client": mlflow_client}
    get_ipython().push(variables=global_variables)

    global_variables_names = "\n- ".join(
        [f"'{key}'" for key in global_variables.keys()]
    )
    logging.info("** Kedro project %s", str(metadata.project_name))
    logging.info("Import mlflow in namespace")
    logging.info("Setup mlflow configuration")
    logging.info(f"Defined global variable(s):\n- {global_variables_names}")
