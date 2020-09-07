import yaml

from kedro_mlflow.framework.context import get_mlflow_config

# def test_get_mlflow_config_outside_kedro_project(tmp_path, config_with_base_mlflow_conf):
#     with pytest.raises(KedroMlflowConfigError, match="not a valid path to a kedro project"):
#         get_mlflow_config(project_path=tmp_path,env="local")


def test_get_mlflow_config(mocker, tmp_path, config_dir):
    # config_with_base_mlflow_conf is a pytest.fixture in conftest
    mocker.patch("kedro_mlflow.utils._is_kedro_project", return_value=True)

    def _write_yaml(filepath, config):
        filepath.parent.mkdir(parents=True, exist_ok=True)
        yaml_str = yaml.dump(config)
        filepath.write_text(yaml_str)

    _write_yaml(
        tmp_path / "conf" / "base" / "mlflow.yml",
        dict(
            mlflow_tracking_uri="mlruns",
            experiment=dict(name="fake_package", create=True),
            run=dict(id="123456789", name="my_run", nested=True),
            ui=dict(port="5151", host="localhost"),
            hooks=dict(node=dict(flatten_dict_params=True, recursive=False, sep="-")),
        ),
    )
    expected = {
        "mlflow_tracking_uri": (tmp_path / "mlruns").as_uri(),
        "experiments": {"name": "fake_package", "create": True},
        "run": {"id": "123456789", "name": "my_run", "nested": True},
        "ui": {"port": "5151", "host": "localhost"},
        "hooks": {
            "node": {"flatten_dict_params": True, "recursive": False, "sep": "-"}
        },
    }
    assert get_mlflow_config(project_path=tmp_path, env="local").to_dict() == expected
