import mlflow
import pytest
import yaml
from kedro.io import DataCatalog, MemoryDataSet
from kedro.pipeline import Pipeline, node
from mlflow.tracking import MlflowClient

from kedro_mlflow.framework.hooks import MlflowNodeHook
from kedro_mlflow.framework.hooks.node_hook import flatten_dict


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
        "run_id": "abcdef",
        "project_path": tmp_path.as_posix(),
        "env": "local",
        "kedro_version": "0.16.0",
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

    def _write_yaml(filepath, config):
        filepath.parent.mkdir(parents=True, exist_ok=True)
        yaml_str = yaml.dump(config)
        filepath.write_text(yaml_str)

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

    def fake_fun(arg1, arg2, arg3):
        return None

    node_test = node(
        func=fake_fun,
        inputs={"arg1": "params:param1", "arg2": "foo", "arg3": "parameters"},
        outputs="out",
    )
    dummy_pipeline = Pipeline([node_test])

    catalog = DataCatalog(
        {
            "params:param1": 1,
            "foo": MemoryDataSet(),
            "bar": MemoryDataSet(),
            "parameters": {"param1": 1, "param2": 2},
        }
    )
    node_inputs = {v: catalog._data_sets.get(v) for k, v in node_test._inputs.items()}

    mlflow_tracking_uri = (tmp_path / "mlruns").as_uri()
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    with mlflow.start_run():
        mlflow_node_hook.before_pipeline_run(
            run_params=dummy_run_params, pipeline=dummy_pipeline, catalog=catalog
        )
        mlflow_node_hook.before_node_run(
            node=node_test,
            catalog=catalog,
            inputs=node_inputs,
            is_async=False,
            run_id="132",
        )
        run_id = mlflow.active_run().info.run_id

    mlflow_client = MlflowClient(mlflow_tracking_uri)
    current_run = mlflow_client.get_run(run_id)
    assert current_run.data.params == expected
