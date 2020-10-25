import re
from pathlib import Path
from typing import Any, Dict, Union

import anyconfig
import yaml
from kedro import __version__ as KEDRO_VERSION
from kedro.framework.context import load_context

KEDRO_YML = ".kedro.yml"


def _is_kedro_project(project_path: Union[str, Path, None] = None) -> bool:
    """Best effort to check if the function is called
     inside a kedro project.

    Returns:
        bool -- True if the working directory is the root of a kedro project
    """
    project_path = _validate_project_path(project_path)
    flag = (project_path / KEDRO_YML).is_file()
    return flag


def _get_project_globals(project_path: Union[str, Path, None]) -> Dict[str, str]:

    # if project_path is None:
    #     project_path = Path.cwd()
    # for the project name, we have to load the context : it is the only place where it is recorded
    project_context = load_context(project_path)
    project_name = project_context.project_name

    kedro_yml = _read_kedro_yml(project_path)
    python_package = re.search(
        pattern=r"^(\w+)(?=\.)", string=kedro_yml["context_path"]
    ).group(1)
    context_path = kedro_yml["context_path"].replace(".", "/")
    return dict(
        context_path=context_path,
        project_name=project_name,
        package_name=python_package,
        kedro_version=KEDRO_VERSION,
    )


def _read_kedro_yml(project_path: Union[str, Path, None] = None) -> Dict[str, str]:
    project_path = _validate_project_path(project_path)
    kedro_yml_path = project_path / KEDRO_YML

    with open(kedro_yml_path, mode="r", encoding="utf-8") as file_handler:
        kedro_yml = yaml.safe_load(file_handler.read())

    return kedro_yml


def _validate_project_path(project_path: Union[str, Path, None] = None) -> Path:
    if project_path is None:
        project_path = Path.cwd()
    else:
        project_path = Path(project_path)
    return project_path


def _already_updated(project_path: Union[str, Path, None] = None) -> bool:
    project_path = _validate_project_path(project_path)
    flag = False
    # TODO : add a better check ...
    if (project_path / "conf" / "base" / "mlflow.yml").is_file():
        flag = True
    return flag


def _parse_requirements(path, encoding="utf-8"):
    with open(path, mode="r", encoding=encoding) as file_handler:
        requirements = [
            x.strip() for x in file_handler if x.strip() and not x.startswith("-r")
        ]
    return requirements


class KedroContextError(Exception):
    """Error occurred when loading project and running context pipeline."""
