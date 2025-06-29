from pathlib import Path
from typing import Union


def _is_project(project_path: Union[str, Path]) -> bool:
    try:
        # untested in the CI, for retrocompatiblity with kedro >=0.19.0,<0.19.3
        from kedro.framework.startup import _is_project as _ip
    except ImportError:
        from kedro.utils import _is_project as _ip

    return _ip(project_path)
