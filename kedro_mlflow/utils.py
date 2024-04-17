from pathlib import Path
from typing import Any, List, Union


def _parse_requirements(path: Union[str, Path], encoding="utf-8") -> List:
    with open(path, encoding=encoding) as file_handler:
        requirements = [
            x.strip() for x in file_handler if x.strip() and not x.startswith("-r")
        ]
    return requirements


def _is_project(project_path: Union[str, Path]) -> bool:
    try:
        # untested in the CI, for retrocompatiblity with kedro >=0.19.0,<0.19.3
        from kedro.framework.startup import _is_project as _ip
    except ImportError:
        from kedro.utils import _is_project as _ip

    return _ip(project_path)


def _find_kedro_project(current_dir: Path) -> Any:
    try:
        # untested in the CI, for retrocompatiblity with kedro >=0.19.0,<0.19.3
        from kedro.framework.startup import _find_kedro_project as _fkp
    except ImportError:
        from kedro.utils import _find_kedro_project as _fkp

    return _fkp(current_dir)
