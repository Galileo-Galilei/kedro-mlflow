import os
from pathlib import Path

import mlflow
import pytest
import yaml
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from kedro.io import DataCatalog, MemoryDataset
from kedro.pipeline import Pipeline, node
from mlflow.tracking import MlflowClient
from mlflow.utils.validation import MAX_PARAM_VAL_LENGTH

from kedro_mlflow.framework.hooks import MlflowHook


def _write_yaml(filepath: Path, config: dict):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    yaml_str = yaml.dump(config)
    filepath.write_text(yaml_str)


@pytest.fixture
def dummy_run_params(tmp_path):
    dummy_run_params = {
        "run_id": "",
        "project_path": tmp_path.as_posix(),
        "env": "local",
        "kedro_version": "0.16.5",
        "tags": [],
        "from_nodes": [],
        "to_nodes": [],
        "node_names": [],
        "from_inputs": [],
        "load_versions": [],
        "pipeline_name": "my_cool_pipeline",
        "extra_params": [],
    }
    return dummy_run_params


@pytest.fixture
def dummy_node():
    def fake_fun(arg1, arg2, arg3):
        return None

    node_test = node(
        func=fake_fun,
        inputs={"arg1": "params:param1", "arg2": "foo", "arg3": "parameters"},
        outputs="out",
    )

    return node_test


@pytest.fixture
def dummy_pipeline(dummy_node):
    dummy_pipeline = Pipeline([dummy_node])

    return dummy_pipeline


@pytest.fixture
def dummy_catalog():
    catalog = DataCatalog(
        {
            "params:param1": 1,
            "foo": MemoryDataset(),
            "bar": MemoryDataset(),
            "parameters": {"param1": 1, "param2": 2},
        }
    )

    return catalog


@pytest.mark.parametrize(
    "param_name,expected_name",
    [
        ("valid_param", "valid_param"),
        ("valid-param", "valid-param"),
        ("invalid/param", "invalid/param"),
        ("invalid.param", "invalid.param"),
        ("[invalid]$param", "_invalid__param"),
    ],
)
def test_parameter_name_sanitization(
    kedro_project, dummy_run_params, param_name, expected_name
):
    mlflow_tracking_uri = (kedro_project / "mlruns").as_uri()
    mlflow.set_tracking_uri(mlflow_tracking_uri)

    node_inputs = {f"params:{param_name}": "test_value"}

    bootstrap_project(kedro_project)
    with KedroSession.create(
        project_path=kedro_project,
    ) as session:
        context = session.load_context()
        mlflow_node_hook = MlflowHook()
        mlflow_node_hook.after_context_created(context)

        with mlflow.start_run():
            mlflow_node_hook.before_pipeline_run(
                run_params=dummy_run_params,
                pipeline=Pipeline([]),
                catalog=DataCatalog(),
            )
            mlflow_node_hook.before_node_run(
                node=node(func=lambda x: x, inputs=dict(x="a"), outputs=None),
                catalog=DataCatalog(),
                inputs=node_inputs,
                is_async=False,
            )
            run_id = mlflow.active_run().info.run_id

        mlflow_client = MlflowClient(mlflow_tracking_uri)
        current_run = mlflow_client.get_run(run_id)
        assert expected_name in current_run.data.params
        assert current_run.data.params[expected_name] == "test_value"


@pytest.mark.skipif(
    os.name != "nt", reason="Windows does not log params with colon symbol"
)
def test_parameter_name_with_colon_sanitization_on_windows(
    kedro_project, dummy_run_params
):
    param_name = "valid:param"
    expected_name = "valid_param"

    mlflow_tracking_uri = (kedro_project / "mlruns").as_uri()
    mlflow.set_tracking_uri(mlflow_tracking_uri)

    node_inputs = {f"params:{param_name}": "test_value"}

    bootstrap_project(kedro_project)
    with KedroSession.create(
        project_path=kedro_project,
    ) as session:
        context = session.load_context()
        mlflow_node_hook = MlflowHook()
        mlflow_node_hook.after_context_created(context)

        with mlflow.start_run():
            mlflow_node_hook.before_pipeline_run(
                run_params=dummy_run_params,
                pipeline=Pipeline([]),
                catalog=DataCatalog(),
            )
            mlflow_node_hook.before_node_run(
                node=node(func=lambda x: x, inputs=dict(x="a"), outputs=None),
                catalog=DataCatalog(),
                inputs=node_inputs,
                is_async=False,
            )
            run_id = mlflow.active_run().info.run_id

        mlflow_client = MlflowClient(mlflow_tracking_uri)
        current_run = mlflow_client.get_run(run_id)
        assert expected_name in current_run.data.params
        assert current_run.data.params[expected_name] == "test_value"


@pytest.mark.skipif(
    os.name == "nt", reason="Linux and Mac do log params with colon symbol"
)
def test_parameter_name_with_colon_sanitization_on_mac_linux(
    kedro_project, dummy_run_params
):
    param_name = "valid:param"
    expected_name = "valid:param"

    mlflow_tracking_uri = (kedro_project / "mlruns").as_uri()
    mlflow.set_tracking_uri(mlflow_tracking_uri)

    node_inputs = {f"params:{param_name}": "test_value"}

    bootstrap_project(kedro_project)
    with KedroSession.create(
        project_path=kedro_project,
    ) as session:
        context = session.load_context()
        mlflow_node_hook = MlflowHook()
        mlflow_node_hook.after_context_created(context)

        with mlflow.start_run():
            mlflow_node_hook.before_pipeline_run(
                run_params=dummy_run_params,
                pipeline=Pipeline([]),
                catalog=DataCatalog(),
            )
            mlflow_node_hook.before_node_run(
                node=node(func=lambda x: x, inputs=dict(x="a"), outputs=None),
                catalog=DataCatalog(),
                inputs=node_inputs,
                is_async=False,
            )
            run_id = mlflow.active_run().info.run_id

        mlflow_client = MlflowClient(mlflow_tracking_uri)
        current_run = mlflow_client.get_run(run_id)
        assert expected_name in current_run.data.params
        assert current_run.data.params[expected_name] == "test_value"


def test_pipeline_run_hook_getting_configs(
    kedro_project,
    dummy_run_params,
    dummy_pipeline,
    dummy_catalog,
):
    _write_yaml(
        kedro_project / "conf" / "local" / "mlflow.yml",
        dict(
            tracking=dict(
                params=dict(dict_params=dict(flatten=True, recursive=False, sep="-")),
            ),
        ),
    )

    bootstrap_project(kedro_project)
    with KedroSession.create(
        project_path=kedro_project,
    ) as session:
        context = session.load_context()

        mlflow_node_hook = MlflowHook()
        mlflow_node_hook.after_context_created(context)
        mlflow_node_hook.before_pipeline_run(
            run_params=dummy_run_params, pipeline=dummy_pipeline, catalog=dummy_catalog
        )

        assert (
            mlflow_node_hook.flatten,
            mlflow_node_hook.recursive,
            mlflow_node_hook.sep,
        ) == (True, False, "-")


@pytest.mark.parametrize(
    "flatten,expected",
    [
        (True, {"param1": "1", "parameters-param1": "1", "parameters-param2": "2"}),
        (False, {"param1": "1", "parameters": "{'param1': 1, 'param2': 2}"}),
    ],
)
def test_node_hook_logging(
    kedro_project,
    dummy_run_params,
    dummy_catalog,
    dummy_pipeline,
    dummy_node,
    flatten,
    expected,
):
    _write_yaml(
        kedro_project / "conf" / "base" / "mlflow.yml",
        dict(
            tracking=dict(
                params=dict(dict_params=dict(flatten=flatten, recursive=False, sep="-"))
            )
        ),
    )

    node_inputs = {v: dummy_catalog.get(v) for k, v in dummy_node._inputs.items()}

    mlflow_tracking_uri = (kedro_project / "mlruns").as_uri()

    bootstrap_project(kedro_project)
    with KedroSession.create(
        project_path=kedro_project,
    ) as session:
        context = session.load_context()
        mlflow_node_hook = MlflowHook()
        mlflow_node_hook.after_context_created(context)  # setup mlflow_config
        mlflow.set_tracking_uri(mlflow_tracking_uri)

        with mlflow.start_run():
            mlflow_node_hook.before_pipeline_run(
                run_params=dummy_run_params,
                pipeline=dummy_pipeline,
                catalog=dummy_catalog,
            )
            mlflow_node_hook.before_node_run(
                node=dummy_node,
                catalog=dummy_catalog,
                inputs=node_inputs,
                is_async=False,
            )
            run_id = mlflow.active_run().info.run_id

        mlflow_client = MlflowClient(mlflow_tracking_uri)
        current_run = mlflow_client.get_run(run_id)
        assert current_run.data.params == expected


@pytest.mark.parametrize(
    "param_length", [MAX_PARAM_VAL_LENGTH - 10, MAX_PARAM_VAL_LENGTH]
)
@pytest.mark.parametrize("strategy", ["fail", "truncate", "tag"])
def test_node_hook_logging_below_limit_all_strategy(
    kedro_project, dummy_run_params, param_length, strategy
):
    _write_yaml(
        kedro_project / "conf" / "local" / "mlflow.yml",
        dict(
            tracking=dict(params=dict(long_params_strategy=strategy)),
        ),
    )

    mlflow_tracking_uri = (kedro_project / "mlruns").as_uri()
    mlflow.set_tracking_uri(mlflow_tracking_uri)

    param_value = param_length * "a"
    node_inputs = {"params:my_param": param_value}

    bootstrap_project(kedro_project)
    with KedroSession.create(
        project_path=kedro_project,
    ) as session:
        context = session.load_context()
        mlflow_node_hook = MlflowHook()
        mlflow_node_hook.after_context_created(context)  # setup mlflow_config

        with mlflow.start_run():
            mlflow_node_hook.before_pipeline_run(
                run_params=dummy_run_params,
                pipeline=Pipeline([]),
                catalog=DataCatalog(),
            )
            mlflow_node_hook.before_node_run(
                node=node(func=lambda x: x, inputs=dict(x="a"), outputs=None),
                catalog=DataCatalog(),  # can be empty
                inputs=node_inputs,
                is_async=False,
            )
            run_id = mlflow.active_run().info.run_id

        mlflow_client = MlflowClient(mlflow_tracking_uri)
        current_run = mlflow_client.get_run(run_id)
        assert current_run.data.params == {"my_param": param_value}


@pytest.mark.parametrize(
    "param_length",
    [MAX_PARAM_VAL_LENGTH + 20],
)
def test_node_hook_logging_above_limit_truncate_strategy(
    kedro_project, dummy_run_params, param_length
):
    _write_yaml(
        kedro_project / "conf" / "local" / "mlflow.yml",
        dict(
            tracking=dict(params=dict(long_params_strategy="truncate")),
        ),
    )

    mlflow_tracking_uri = (kedro_project / "mlruns").as_uri()
    mlflow.set_tracking_uri(mlflow_tracking_uri)

    param_value = param_length * "a"
    node_inputs = {"params:my_param": param_value}

    bootstrap_project(kedro_project)
    with KedroSession.create(
        project_path=kedro_project,
    ) as session:
        context = session.load_context()
        mlflow_node_hook = MlflowHook()
        mlflow_node_hook.after_context_created(context)
        with mlflow.start_run():
            mlflow_node_hook.before_pipeline_run(
                run_params=dummy_run_params,
                pipeline=Pipeline([]),
                catalog=DataCatalog(),
            )
            mlflow_node_hook.before_node_run(
                node=node(func=lambda x: x, inputs=dict(x="a"), outputs=None),
                catalog=DataCatalog(),  # can be empty
                inputs=node_inputs,
                is_async=False,
            )
            run_id = mlflow.active_run().info.run_id

        mlflow_client = MlflowClient(mlflow_tracking_uri)
        current_run = mlflow_client.get_run(run_id)
        assert current_run.data.params == {
            "my_param": param_value[0:MAX_PARAM_VAL_LENGTH]
        }


@pytest.mark.parametrize(
    "param_length",
    [MAX_PARAM_VAL_LENGTH + 20],
)
def test_node_hook_logging_above_limit_fail_strategy(
    kedro_project, dummy_run_params, param_length
):
    _write_yaml(
        kedro_project / "conf" / "local" / "mlflow.yml",
        dict(
            tracking=dict(
                params=dict(long_params_strategy="fail"),
            ),
        ),
    )

    mlflow_tracking_uri = (kedro_project / "mlruns").as_uri()
    mlflow.set_tracking_uri(mlflow_tracking_uri)

    mlflow_node_hook = MlflowHook()

    param_value = param_length * "a"
    node_inputs = {"params:my_param": param_value}

    bootstrap_project(kedro_project)
    with KedroSession.create(
        project_path=kedro_project,
    ) as session:
        context = session.load_context()
        mlflow_node_hook.after_context_created(context)

        with mlflow.start_run():
            mlflow_node_hook.before_pipeline_run(
                run_params=dummy_run_params,
                pipeline=Pipeline([]),
                catalog=DataCatalog(),
            )

            # IMPORTANT: Overpassing the parameters limit
            # should raise an error for all mlflow backend
            # but it does not on FileStore backend :
            # https://github.com/mlflow/mlflow/issues/2814#issuecomment-628284425
            # Since we use FileStore system for simplicty for tests logging works
            # But we have enforced failure (which is slightly different from mlflow
            # behaviour)
            with pytest.raises(
                ValueError, match=f"Parameter 'my_param' length is {param_length}"
            ):
                mlflow_node_hook.before_node_run(
                    node=node(func=lambda x: x, inputs=dict(x="a"), outputs=None),
                    catalog=DataCatalog(),  # can be empty
                    inputs=node_inputs,
                    is_async=False,
                )


@pytest.mark.parametrize(
    "param_length",
    [MAX_PARAM_VAL_LENGTH + 20],
)
def test_node_hook_logging_above_limit_tag_strategy(
    kedro_project, dummy_run_params, param_length
):
    _write_yaml(
        kedro_project / "conf" / "local" / "mlflow.yml",
        dict(
            tracking=dict(params=dict(long_params_strategy="tag")),
        ),
    )

    mlflow_tracking_uri = (kedro_project / "mlruns").as_uri()
    mlflow.set_tracking_uri(mlflow_tracking_uri)

    mlflow_node_hook = MlflowHook()

    param_value = param_length * "a"
    node_inputs = {"params:my_param": param_value}

    bootstrap_project(kedro_project)
    with KedroSession.create(
        project_path=kedro_project,
    ) as session:
        context = session.load_context()
        mlflow_node_hook.after_context_created(context)
        with mlflow.start_run():
            mlflow_node_hook.before_pipeline_run(
                run_params=dummy_run_params,
                pipeline=Pipeline([]),
                catalog=DataCatalog(),
            )

            # IMPORTANT: Overpassing the parameters limit
            # should raise an error for all mlflow backend
            # but it does not on FileStore backend :
            # https://github.com/mlflow/mlflow/issues/2814#issuecomment-628284425
            # Since we use FileStore system for simplicty for tests logging works
            # But we have enforced failure (which is slightly different from mlflow
            # behaviour)
            mlflow_node_hook.before_node_run(
                node=node(func=lambda x: x, inputs=dict(x="a"), outputs=None),
                catalog=DataCatalog(),  # can be empty
                inputs=node_inputs,
                is_async=False,
            )
            run_id = mlflow.active_run().info.run_id

        mlflow_client = MlflowClient(mlflow_tracking_uri)
        current_run = mlflow_client.get_run(run_id)
        assert current_run.data.params == {}
        assert current_run.data.tags["my_param"] == param_value
