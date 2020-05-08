from kedro.pipeline import Pipeline

from .pipeline_ml import PipelineML


def pipeline_ml(
    training: Pipeline, inference: Pipeline, input_name: str = None,
) -> PipelineML:
    pipeline = PipelineML(
        nodes=training.nodes, inference=inference, input_name=input_name
    )
    return pipeline
