import sys
from pathlib import Path
from typing import Any, Dict, Union

import yaml
from kedro.pipeline import Pipeline

from kedro_mlflow.pipeline import PipelineML


def pipeline_ml(
    training: Pipeline,
    inference: Pipeline,
    env: Union[str, Path, Dict[str, Any]] = None,
    instance_name: str = None,
) -> PipelineML:
    pipeline = PipelineML(nodes=training.nodes, inference=inference)
    return pipeline
