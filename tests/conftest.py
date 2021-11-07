import shutil

import mlflow
import pytest
from cookiecutter.main import cookiecutter
from kedro import __version__ as kedro_version
from kedro.framework.cli.starters import TEMPLATE_PATH
from kedro.framework.hooks.manager import get_hook_manager
from kedro.framework.session.session import _deactivate_session

from kedro_mlflow.framework.cli.cli import TEMPLATE_FOLDER_PATH
from kedro_mlflow.framework.cli.cli_utils import write_jinja_template


@pytest.fixture(autouse=True)
def cleanup_mlflow_after_runs():
    # A test function will be run at this point
    yield
    while mlflow.active_run():
        mlflow.end_run()
    mlflow.set_experiment("Default")


@pytest.fixture(autouse=True)
def cleanup_kedro_session():
    # A test function will be run at this point
    yield
    _deactivate_session()


@pytest.fixture(autouse=True)
def clear_hook_manager():
    yield
    hook_manager = get_hook_manager()
    plugins = hook_manager.get_plugins()
    for plugin in plugins:
        hook_manager.unregister(plugin)


@pytest.fixture
def kedro_project(tmp_path):
    # TODO : this is also an integration test since this depends from the kedro version
    config = {
        "output_dir": tmp_path,
        "kedro_version": kedro_version,
        "project_name": "This is a fake project",
        "repo_name": "fake-project",
        "python_package": "fake_project",
        "include_example": True,
    }

    cookiecutter(
        str(TEMPLATE_PATH),
        output_dir=config["output_dir"],
        no_input=True,
        extra_context=config,
    )

    shutil.rmtree(
        tmp_path / "fake-project" / "src" / "tests"
    )  # avoid conflicts with pytest

    return tmp_path / "fake-project"


@pytest.fixture
def kedro_project_with_mlflow_conf(kedro_project):
    write_jinja_template(
        src=TEMPLATE_FOLDER_PATH / "mlflow.yml",
        is_cookiecutter=False,
        dst=kedro_project / "conf" / "local" / "mlflow.yml",
        python_package="fake_project",
    )

    return kedro_project


@pytest.fixture
def kedro_project_with_tcl(tmp_path):
    # TODO: find a better way to inject dynamically
    # the templated config loader without modifying the template

    config = {
        "output_dir": tmp_path,
        "kedro_version": kedro_version,
        "project_name": "A kedro project with a templated config loader",
        "repo_name": "kedro-project-with-tcl",
        "python_package": "kedro_project_with_tcl",
        "include_example": True,
    }

    cookiecutter(
        str(TEMPLATE_PATH),
        output_dir=config["output_dir"],
        no_input=True,
        extra_context=config,
    )

    shutil.rmtree(
        tmp_path / config["repo_name"] / "src" / "tests"
    )  # avoid conflicts with pytest

    hooks_py = """
from typing import Any, Dict, Iterable, Optional

from kedro.config import TemplatedConfigLoader
from kedro.framework.hooks import hook_impl
from kedro.io import DataCatalog
from kedro.pipeline import Pipeline
from kedro.versioning import Journal


class ProjectHooks:
    @hook_impl
    def register_pipelines(self) -> Dict[str, Pipeline]:
        return {"__default__": Pipeline([])}

    @hook_impl
    def register_config_loader(self, conf_paths: Iterable[str]) -> TemplatedConfigLoader:
        return TemplatedConfigLoader(
            conf_paths,
            globals_pattern="*globals.yml",
            globals_dict={}
        )

    @hook_impl
    def register_catalog(
        self,
        catalog: Optional[Dict[str, Dict[str, Any]]],
        credentials: Dict[str, Dict[str, Any]],
        load_versions: Dict[str, str],
        save_version: str,
        journal: Journal,
    ) -> DataCatalog:
        return DataCatalog.from_config(
            catalog, credentials, load_versions, save_version, journal
        )
"""

    def _write_py(filepath, txt):
        filepath.write_text(txt)

    kedro_project_with_tcl = tmp_path / config["repo_name"]

    _write_py(
        kedro_project_with_tcl / "src" / config["python_package"] / "hooks.py", hooks_py
    )

    return kedro_project_with_tcl
