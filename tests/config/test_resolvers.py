import re

import pytest
import yaml
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from mlflow.utils.name_utils import (
    _GENERATOR_NOUNS,
    _GENERATOR_PREDICATES,
)
from omegaconf import OmegaConf

from kedro_mlflow.config.resolvers import resolve_random_name


def _write_yaml(filepath, config):
    yaml_str = yaml.dump(config)
    filepath.write_text(yaml_str)


def _is_mlflow_name(name: str) -> bool:
    splitted_name = name.split("-")
    flag1 = len(splitted_name) == 3  # noqa: PLR2004
    flag2 = splitted_name[0] in _GENERATOR_PREDICATES
    flag3 = splitted_name[1] in _GENERATOR_NOUNS
    flag4 = re.search(pattern=r"^\d+$", string=splitted_name[2])
    return all({flag1, flag2, flag3, flag4})


@pytest.fixture
def kedro_project_with_random_name(kedro_project):
    # kedro_project is a pytest.fixture in conftest
    dict_config = dict(
        server=dict(
            mlflow_tracking_uri="mlruns",
            mlflow_registry_uri=None,
            credentials=None,
            request_header_provider=dict(type=None, pass_context=False, init_kwargs={}),
        ),
        tracking=dict(
            disable_tracking=dict(pipelines=["my_disabled_pipeline"]),
            experiment=dict(name="fake_package", restore_if_deleted=True),
            run=dict(id="123456789", name="${km.random_name:}", nested=True),
            params=dict(
                dict_params=dict(
                    flatten=True,
                    recursive=False,
                    sep="-",
                ),
                long_params_strategy="truncate",
            ),
        ),
        ui=dict(port="5151", host="localhost"),
    )

    _write_yaml(kedro_project / "conf" / "local" / "mlflow.yml", dict_config)
    expected = dict_config.copy()
    expected["server"]["mlflow_tracking_uri"] = (kedro_project / "mlruns").as_uri()
    return kedro_project


def test_resolve_random_name_is_valid_mlflow_name():
    random_name = resolve_random_name()
    assert _is_mlflow_name(random_name)


def test_resolve_random_name_is_registered(kedro_project_with_random_name):
    bootstrap_project(kedro_project_with_random_name)
    with KedroSession.create(project_path=kedro_project_with_random_name) as session:
        session.load_context()
        assert OmegaConf.has_resolver("km.random_name")


def test_resolve_random_name_is_called_in_project(kedro_project_with_random_name):
    bootstrap_project(kedro_project_with_random_name)
    with KedroSession.create(project_path=kedro_project_with_random_name) as session:
        context = session.load_context()
        assert _is_mlflow_name(context.mlflow.tracking.run.name)


@pytest.mark.skip(reason="kedro 0.19.2 does not take use_cache into account")
def test_resolve_random_name_is_idempotent(kedro_project_with_random_name):
    bootstrap_project(kedro_project_with_random_name)
    with KedroSession.create(project_path=kedro_project_with_random_name) as session:
        context = session.load_context()
        assert (
            context.config_loader["mlflow"]["tracking"]["run"]["name"]
            == context.config_loader["mlflow"]["tracking"]["run"]["name"]
        )  # when called twice, should be different is no use_cache because the resolver is random
