from pathlib import Path
from typing import Dict

import mlflow
import pytest
import yaml
from kedro.io import DataCatalog, MemoryDataSet
from kedro.pipeline import Pipeline, node
from mlflow.tracking import MlflowClient
from mlflow.utils.validation import MAX_PARAM_VAL_LENGTH

from kedro_mlflow.framework.hooks import MlflowNodeHook
from kedro_mlflow.framework.hooks.node_hook import flatten_dict


def _write_yaml(filepath: Path, config: Dict):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    yaml_str = yaml.dump(config)
    filepath.write_text(yaml_str)


def test_flatten_dict_non_nested():
    d = dict(a=1, b=2)
    assert flatten_dict(d=d, recursive=True, sep=".") == d
    assert flatten_dict(d=d, recursive=False, sep=".") == d


def test_flatten_dict_nested_1_level():
    d = dict(a=1, b=dict(c=3, d=4))
    flattened = {"a": 1, "b.c": 3, "b.d": 4}
    assert flatten_dict(d=d, recursive=True, sep=".") == flattened
    assert flatten_dict(d=d, recursive=False, sep=".") == flattened


def test_flatten_dict_nested_2_levels():
    d = dict(a=1, b=dict(c=1, d=dict(e=3, f=5)))

    assert flatten_dict(d=d, recursive=True, sep=".") == {
        "a": 1,
        "b.c": 1,
        "b.d.e": 3,
        "b.d.f": 5,
    }
    assert flatten_dict(d=d, recursive=False, sep=".") == {
        "a": 1,
        "b.c": 1,
        "b.d": {"e": 3, "f": 5},
    }


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
            "foo": MemoryDataSet(),
            "bar": MemoryDataSet(),
            "parameters": {"param1": 1, "param2": 2},
        }
    )

    return catalog


def test_pipeline_run_hook_getting_configs(
    tmp_path, config_dir, monkeypatch, dummy_run_params, dummy_pipeline, dummy_catalog
):

    monkeypatch.chdir(tmp_path)

    _write_yaml(
        tmp_path / "conf" / "base" / "mlflow.yml",
        dict(
            hooks=dict(node=dict(flatten_dict_params=True, recursive=False, sep="-")),
        ),
    ),

    mlflow_node_hook = MlflowNodeHook()
    mlflow_node_hook.before_pipeline_run(
        run_params=dummy_run_params, pipeline=dummy_pipeline, catalog=dummy_catalog
    )

    assert (
        mlflow_node_hook.flatten,
        mlflow_node_hook.recursive,
        mlflow_node_hook.sep,
    ) == (True, False, "-")


@pytest.mark.parametrize(
    "flatten_dict_params,expected",
    [
        (True, {"param1": "1", "parameters-param1": "1", "parameters-param2": "2"}),
        (False, {"param1": "1", "parameters": "{'param1': 1, 'param2': 2}"}),
    ],
)
def test_node_hook_logging(
    tmp_path,
    mocker,
    monkeypatch,
    dummy_run_params,
    dummy_catalog,
    dummy_pipeline,
    dummy_node,
    config_dir,
    flatten_dict_params,
    expected,
):

    mocker.patch("logging.config.dictConfig")
    mocker.patch("kedro_mlflow.utils._is_kedro_project", return_value=True)
    monkeypatch.chdir(tmp_path)
    # config = KedroMlflowConfig(
    #     project_path=tmp_path,
    #     node_hook_opts={"flatten_dict_params": flatten_dict_params, "sep": "-"},
    # )
    # # the function is imported inside the other file antd this is the file to patch
    # # see https://stackoverflow.com/questions/30987973/python-mock-patch-doesnt-work-as-expected-for-public-method
    # mocker.patch(
    #     "kedro_mlflow.framework.hooks.node_hook.get_mlflow_config", return_value=config
    # )

    _write_yaml(
        tmp_path / "conf" / "base" / "mlflow.yml",
        dict(
            hooks=dict(
                node=dict(
                    flatten_dict_params=flatten_dict_params, recursive=False, sep="-"
                )
            ),
        ),
    ),

    mlflow_node_hook = MlflowNodeHook()

    node_inputs = {
        v: dummy_catalog._data_sets.get(v) for k, v in dummy_node._inputs.items()
    }

    mlflow_tracking_uri = (tmp_path / "mlruns").as_uri()
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    with mlflow.start_run():
        mlflow_node_hook.before_pipeline_run(
            run_params=dummy_run_params, pipeline=dummy_pipeline, catalog=dummy_catalog
        )
        mlflow_node_hook.before_node_run(
            node=dummy_node,
            catalog=dummy_catalog,
            inputs=node_inputs,
            is_async=False,
            run_id="132",
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
    tmp_path, config_dir, dummy_run_params, dummy_node, param_length, strategy
):

    # mocker.patch("kedro_mlflow.utils._is_kedro_project", return_value=True)

    _write_yaml(
        tmp_path / "conf" / "base" / "mlflow.yml",
        dict(
            hooks=dict(node=dict(long_parameters_strategy=strategy)),
        ),
    )

    mlflow_tracking_uri = (tmp_path / "mlruns").as_uri()
    mlflow.set_tracking_uri(mlflow_tracking_uri)

    mlflow_node_hook = MlflowNodeHook()

    param_value = param_length * "a"
    node_inputs = {"params:my_param": param_value}

    with mlflow.start_run():
        mlflow_node_hook.before_pipeline_run(
            run_params=dummy_run_params, pipeline=Pipeline([]), catalog=DataCatalog()
        )
        mlflow_node_hook.before_node_run(
            node=node(func=lambda x: x, inputs=dict(x="a"), outputs=None),
            catalog=DataCatalog(),  # can be empty
            inputs=node_inputs,
            is_async=False,
            run_id="132",
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
    tmp_path, config_dir, dummy_run_params, dummy_node, param_length
):

    # mocker.patch("kedro_mlflow.utils._is_kedro_project", return_value=True)

    _write_yaml(
        tmp_path / "conf" / "base" / "mlflow.yml",
        dict(
            hooks=dict(node=dict(long_parameters_strategy="truncate")),
        ),
    )

    mlflow_tracking_uri = (tmp_path / "mlruns").as_uri()
    mlflow.set_tracking_uri(mlflow_tracking_uri)

    mlflow_node_hook = MlflowNodeHook()

    param_value = param_length * "a"
    node_inputs = {"params:my_param": param_value}

    with mlflow.start_run():
        mlflow_node_hook.before_pipeline_run(
            run_params=dummy_run_params, pipeline=Pipeline([]), catalog=DataCatalog()
        )
        mlflow_node_hook.before_node_run(
            node=node(func=lambda x: x, inputs=dict(x="a"), outputs=None),
            catalog=DataCatalog(),  # can be empty
            inputs=node_inputs,
            is_async=False,
            run_id="132",
        )
        run_id = mlflow.active_run().info.run_id

    mlflow_client = MlflowClient(mlflow_tracking_uri)
    current_run = mlflow_client.get_run(run_id)
    assert current_run.data.params == {"my_param": param_value[0:MAX_PARAM_VAL_LENGTH]}


@pytest.mark.parametrize(
    "param_length",
    [MAX_PARAM_VAL_LENGTH + 20],
)
def test_node_hook_logging_above_limit_fail_strategy(
    tmp_path, config_dir, dummy_run_params, dummy_node, param_length
):

    # mocker.patch("kedro_mlflow.utils._is_kedro_project", return_value=True)

    _write_yaml(
        tmp_path / "conf" / "base" / "mlflow.yml",
        dict(
            hooks=dict(node=dict(long_parameters_strategy="fail")),
        ),
    )

    mlflow_tracking_uri = (tmp_path / "mlruns").as_uri()
    mlflow.set_tracking_uri(mlflow_tracking_uri)

    mlflow_node_hook = MlflowNodeHook()

    param_value = param_length * "a"
    node_inputs = {"params:my_param": param_value}

    with mlflow.start_run():
        mlflow_node_hook.before_pipeline_run(
            run_params=dummy_run_params, pipeline=Pipeline([]), catalog=DataCatalog()
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
                run_id="132",
            )


@pytest.mark.parametrize(
    "param_length",
    [MAX_PARAM_VAL_LENGTH + 20],
)
def test_node_hook_logging_above_limit_tag_strategy(
    tmp_path, config_dir, dummy_run_params, dummy_node, param_length
):

    # mocker.patch("kedro_mlflow.utils._is_kedro_project", return_value=True)

    _write_yaml(
        tmp_path / "conf" / "base" / "mlflow.yml",
        dict(
            hooks=dict(node=dict(long_parameters_strategy="tag")),
        ),
    )

    mlflow_tracking_uri = (tmp_path / "mlruns").as_uri()
    mlflow.set_tracking_uri(mlflow_tracking_uri)

    mlflow_node_hook = MlflowNodeHook()

    param_value = param_length * "a"
    node_inputs = {"params:my_param": param_value}

    with mlflow.start_run():
        mlflow_node_hook.before_pipeline_run(
            run_params=dummy_run_params, pipeline=Pipeline([]), catalog=DataCatalog()
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
            run_id="132",
        )
        run_id = mlflow.active_run().info.run_id

    mlflow_client = MlflowClient(mlflow_tracking_uri)
    current_run = mlflow_client.get_run(run_id)
    assert current_run.data.params == {}
    assert {
        k: v for k, v in current_run.data.tags.items() if not k.startswith("mlflow")
    } == {"my_param": param_value}
