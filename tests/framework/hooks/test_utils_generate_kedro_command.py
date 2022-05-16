import pytest

from kedro_mlflow.framework.hooks.utils import _generate_kedro_command


def test_generate_kedro_commands():
    # TODO : add a better test because the formatting of record_data is subject to change
    # We could check that the command is recored and then rerun properly
    record_data = {
        "tags": ["tag1", "tag2"],
        "from_nodes": ["node1"],
        "to_nodes": ["node3"],
        "node_names": ["node1", "node2", "node1"],
        "from_inputs": ["data_in"],
        "load_versions": {"data_inter": "01:23:45"},
        "pipeline_name": "fake_pl",
    }

    expected = "kedro run --from-inputs=data_in --from-nodes=node1 --to-nodes=node3 --node=node1,node2,node1 --pipeline=fake_pl --tag=tag1,tag2 --load-version=data_inter:01:23:45"
    assert _generate_kedro_command(**record_data) == expected


@pytest.mark.parametrize("default_value", [None, []])
def test_generate_default_kedro_commands(default_value):
    """This test ensures that the _generate_kedro_comands accepts both
     `None` and empty `list` as default value, because CLI and interactive
     `Journal` do not use the same default.

    Args:
        default_value ([type]): [description]
    """
    record_data = {
        "tags": default_value,
        "from_nodes": default_value,
        "to_nodes": default_value,
        "node_names": default_value,
        "from_inputs": default_value,
        "load_versions": default_value,
        "pipeline_name": "fake_pl",
    }

    expected = "kedro run --pipeline=fake_pl"
    assert _generate_kedro_command(**record_data) == expected
