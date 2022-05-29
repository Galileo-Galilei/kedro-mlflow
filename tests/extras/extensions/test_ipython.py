import pytest
from kedro.framework.session.session import KedroSession
from kedro.framework.startup import bootstrap_project

from kedro_mlflow.extras.extensions.ipython import reload_kedro_mlflow


@pytest.fixture(autouse=True)
def mocked_logging(mocker):
    # Disable logging.config.dictConfig in KedroSession._setup_logging as
    # it changes logging.config and affects other unit tests
    return mocker.patch("logging.config.dictConfig")


def test_load_global_variables_in_ipython(mocker, kedro_project_with_mlflow_conf):

    mock_ipython = mocker.patch("kedro_mlflow.extras.extensions.ipython.get_ipython")
    mocker.patch("kedro.framework.session.session.KedroSession._setup_logging")

    metadata = bootstrap_project(kedro_project_with_mlflow_conf)
    with KedroSession.create(
        metadata.package_name, project_path=metadata.project_path
    ) as session:
        context = session.load_context()
        reload_kedro_mlflow(
            line=None,
            local_ns={"project_path": metadata.project_path, "context": context},
        )

    mock_ipython().push.assert_called_once_with(variables={"mlflow_client": mocker.ANY})
