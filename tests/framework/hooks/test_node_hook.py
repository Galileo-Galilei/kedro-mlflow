import mlflow
from kedro.io import DataCatalog, MemoryDataSet
from kedro.pipeline import node
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


def test_node_hook(tmp_path):
    mlflow_node_hook = MlflowNodeHook(flatten_dict_params=True, recursive=True, sep="-")

    def fake_fun(arg1, arg2, arg3):
        return None

    node_test = node(
        func=fake_fun,
        inputs={"arg1": "params:param1", "arg2": "foo", "arg3": "parameters"},
        outputs="out",
    )
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
    assert current_run.data.params == {
        "param1": "1",
        "parameters-param1": "1",
        "parameters-param2": "2",
    }
