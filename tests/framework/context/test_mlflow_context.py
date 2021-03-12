import pytest
import yaml
from kedro.framework.session import KedroSession
from kedro.framework.startup import _get_project_metadata

from kedro_mlflow.framework.context import get_mlflow_config
from kedro_mlflow.framework.context.config import KedroMlflowConfigError


def _write_yaml(filepath, config):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    yaml_str = yaml.dump(config)
    filepath.write_text(yaml_str)


# TODO : reenable this test which is currently failing beacause kedro "import settings"
# is completetly messing up because we have several projects
# and the first import wins

# import shutil
# from cookiecutter.main import cookiecutter
# from kedro import __version__ as kedro_version
# from kedro.framework.cli.cli import TEMPLATE_PATH
# from kedro.framework.cli.utils import _add_src_to_path

# @pytest.fixture
# def kedro_project_with_tcl(tmp_path):
#     # TODO: find a better way to inject dynamically
#     # the templated config loader without modifying the template

#     config = {
#         "output_dir": tmp_path,
#         "kedro_version": kedro_version,
#         "project_name": "This is a kedro project with a TemplatedConfigLoader",
#         "repo_name": "kedro-project-tcl",
#         "python_package": "kedro_project_tcl",
#         "include_example": True,
#     }

#     cookiecutter(
#         str(TEMPLATE_PATH),
#         output_dir=config["output_dir"],
#         no_input=True,
#         extra_context=config,
#     )

#     shutil.rmtree(
#         tmp_path / "kedro-project-tcl" / "src" / "tests"
#     )  # avoid conflicts with pytest

#     kedro_project_with_tcl = tmp_path / "kedro-project-tcl"
#     hooks_py = """
# from typing import Any, Dict, Iterable, Optional

# from kedro.config import TemplatedConfigLoader
# from kedro.framework.hooks import hook_impl
# from kedro.io import DataCatalog
# from kedro.pipeline import Pipeline
# from kedro.versioning import Journal


# class ProjectHooks:
#     @hook_impl
#     def register_pipelines(self) -> Dict[str, Pipeline]:
#         return {"__default__": Pipeline([])}

#     @hook_impl
#     def register_config_loader(self, conf_paths: Iterable[str]) -> TemplatedConfigLoader:
#         return TemplatedConfigLoader(
#             conf_paths,
#             globals_pattern="*globals.yml",
#             globals_dict={}
#         )

#     @hook_impl
#     def register_catalog(
#         self,
#         catalog: Optional[Dict[str, Dict[str, Any]]],
#         credentials: Dict[str, Dict[str, Any]],
#         load_versions: Dict[str, str],
#         save_version: str,
#         journal: Journal,
#     ) -> DataCatalog:
#         return DataCatalog.from_config(
#             catalog, credentials, load_versions, save_version, journal
#         )
# """

#     def _write_py(filepath, txt):
#         filepath.parent.mkdir(parents=True, exist_ok=True)
#         filepath.write_text(txt)

#     metadata = _get_project_metadata(kedro_project_with_tcl)
#     _write_py(
#         kedro_project_with_tcl / "src" / metadata.package_name / "hooks.py", hooks_py
#     )

#     return kedro_project_with_tcl


def test_get_mlflow_config(kedro_project):
    # kedro_project is a pytest.fixture in conftest

    _write_yaml(
        kedro_project / "conf" / "local" / "mlflow.yml",
        dict(
            mlflow_tracking_uri="mlruns",
            credentials=None,
            experiment=dict(name="fake_package", create=True),
            run=dict(id="123456789", name="my_run", nested=True),
            ui=dict(port="5151", host="localhost"),
            hooks=dict(
                node=dict(
                    flatten_dict_params=True,
                    recursive=False,
                    sep="-",
                    long_parameters_strategy="truncate",
                )
            ),
        ),
    )
    expected = {
        "mlflow_tracking_uri": (kedro_project / "mlruns").as_uri(),
        "credentials": None,
        "experiments": {"name": "fake_package", "create": True},
        "run": {"id": "123456789", "name": "my_run", "nested": True},
        "ui": {"port": "5151", "host": "localhost"},
        "hooks": {
            "node": {
                "flatten_dict_params": True,
                "recursive": False,
                "sep": "-",
                "long_parameters_strategy": "truncate",
            }
        },
    }

    with KedroSession.create("fake_project", project_path=kedro_project):
        assert get_mlflow_config().to_dict() == expected


def test_get_mlflow_config_in_uninitialized_project(kedro_project):
    # config_with_base_mlflow_conf is a pytest.fixture in conftest
    metadata = _get_project_metadata(kedro_project)
    with pytest.raises(
        KedroMlflowConfigError, match="No 'mlflow.yml' config file found in environment"
    ):
        with KedroSession.create(metadata.package_name, kedro_project):
            get_mlflow_config()


# TODO : reenable this test which is currently failing beacause kedro "import settings"
# is completetly messing up beacuase we have several projects
# and the first imort wins

# def test_mlflow_config_with_templated_config_loader(
#     kedro_project_with_tcl,
# ):

#     _write_yaml(
#         kedro_project_with_tcl / "conf" / "local" / "mlflow.yml",
#         dict(
#             mlflow_tracking_uri="${mlflow_tracking_uri}",
#             credentials=None,
#             experiment=dict(name="fake_package", create=True),
#             run=dict(id="123456789", name="my_run", nested=True),
#             ui=dict(port="5151", host="localhost"),
#             hooks=dict(
#                 node=dict(
#                     flatten_dict_params=True,
#                     recursive=False,
#                     sep="-",
#                     long_parameters_strategy="truncate",
#                 )
#             ),
#         ),
#     )

#     _write_yaml(
#         kedro_project_with_tcl / "conf" / "local" / "globals.yml",
#         dict(mlflow_tracking_uri="dynamic_mlruns"),
#     )

#     expected = {
#         "mlflow_tracking_uri": (kedro_project_with_tcl / "dynamic_mlruns").as_uri(),
#         "credentials": None,
#         "experiments": {"name": "fake_package", "create": True},
#         "run": {"id": "123456789", "name": "my_run", "nested": True},
#         "ui": {"port": "5151", "host": "localhost"},
#         "hooks": {
#             "node": {
#                 "flatten_dict_params": True,
#                 "recursive": False,
#                 "sep": "-",
#                 "long_parameters_strategy": "truncate",
#             }
#         },
#     }
#     metadata = _get_project_metadata(kedro_project_with_tcl)
#     _add_src_to_path(metadata.source_dir, kedro_project_with_tcl)
#     with KedroSession.create(metadata.package_name, kedro_project_with_tcl):
#         assert get_mlflow_config().to_dict() == expected
