from typing import Iterable, Union, Callable, Any, Dict

from kedro.pipeline import Pipeline
from kedro.pipeline.node import Node
from pathlib import Path


class PipelineML(Pipeline):
    """
    IMPORTANT NOTE : THIS CLASS IS NOT INTENDED TO BE USED DIRECTLY IN A KEDRO PROJECT. YOU SHOULD USE
    ``pipeline_ml`` FUNCTION FOR MODULAR PIPELINE WHICH IS MORE FLEXIBLE AND USER FRIENDLY.
    SEE INSERT_DOC_URL
    A ``PipelineML`` is a kedro ``Pipeline`` which we assume is a "training" (in the machine learning way)
    pipeline. Basically, training is a higher order function (it generates another function). It implies that:
    -  the outputs of this pipeline are considered as "fitted models", i.e. inputs
    of another inference pipeline (it is very likely that tere are several outputs because we any object
    that depends on the train data (e.g encoders, binarizers, vectorizer, machine learning models...)
    - These outputs will feed another "inference" pipeline (to be used for prediction purpose) whose inputs
     are the outpust of the "training" pipeline, except for one of them (the data to predict).

     This class enables to "link" a training pipeline and an inference pipeline in order to package them
     in mlflow easily. The goal is to call the ``MLflowPipelineSpec`` hook after a PipelineMl is called
     in order to trigger mlflow packaging.


    Arguments:
        Pipeline {[type]} -- [description]
    """

    def __init__(
        self,
        nodes: Iterable[Union[Node, "Pipeline"]],
        *args,
        inference: Pipeline,
        conda_env: Union[str, None, Path],
        tags: Union[str, Iterable[str]] = None):
    
        super.__init__(nodes, *args, tags=tags)
        self.inference = inference
        self.conda_env = self._format_conda_env(conda_env)

    def _format_conda_env(self, conda_env=None) -> Dict[str, Any]:
        """Best effort to get dependecies of the project.

        Keyword Arguments:
            conda_env {[type]} -- It can be either :
                - a path to a "requirements.txt": In this case
                the packages are parsed and a conda env with
                your current python_version and these dependencies is returned
                - a path to an "environment.yml" : data is loaded and used as they are
                - a Dict : used as the environment
                - None (default: {None}) : try to infer the dependencies base on current package name

        Returns:
            Dict[str, Any] -- [description]
        """
        if isinstance(conda_env, str):
            conda_env = pathlib.Path(conda_env)
        if isinstance(conda_env, pathlib.Path):
            if conda_env.suffix in (".yml", ".yaml"):
                with open(conda_env, mode="r") as file_handler:
                    conda_env = yaml.safe_load(conda_env)
            elif conda_env.suffix in (".txt"):
                with open(conda_env, mode="r") as file_handler:
                    dependencies = _parse_requirements(conda_env)
                conda_env = {"python": sys.version,
                             "dependencies": dependencies}
        else:
            try:
                conda_env = {"python": sys.version,
                             "dependencies": _get_project_globals(project_globals["python_package"])}
            except:
                conda_env = {"python": sys.version,
                             "dependencies": [project_globals["python_package"]]}

        return conda_env

    def only_nodes_with_inputs(self, *inputs: str) -> "PipelineML":
        pipeline = super().only_nodes_with_inputs(*inputs)
        return self._turn_pipeline_to_ml(pipeline)

    def from_inputs(self, *inputs: str) -> "PipelineML":
        pipeline = super().from_inputs(*inputs)
        return self._turn_pipeline_to_ml(pipeline)

    def only_nodes_with_outputs(self, *outputs: str) -> "PipelineML":
        pipeline = super().only_nodes_with_outputs(*outputs)
        return self._turn_pipeline_to_ml(pipeline)

    def to_outputs(self, *outputs: str) -> "PipelineML":
        pipeline = super().to_outputs(*outputs)
        return self._turn_pipeline_to_ml(pipeline)

    def from_nodes(self, *node_names: str) -> "PipelineML":
        pipeline = super().from_nodes(*node_names)
        return self._turn_pipeline_to_ml(pipeline)

    def to_nodes(self, *node_names: str) -> "PipelineML":
        pipeline = super().to_nodes(*node_names)
        return self._turn_pipeline_to_ml(pipeline)

    def only_nodes_with_tags(self, *tags: str) -> "PipelineML":
        pipeline = super().only_nodes_with_tags(*tags)
        return self._turn_pipeline_to_ml(pipeline)

    def decorate(self, *decorators: Callable) -> "PipelineML":
        pipeline = super().decorate(*decorators)
        return self._turn_pipeline_to_ml(pipeline)

    def tag(self, tags: Union[str, Iterable[str]]) -> "PipelineML":
        pipeline = super().tag(*tags)
        return self._turn_pipeline_to_ml(pipeline)

    def _turn_pipeline_to_ml(self, pipeline):
        return PipelineML(nodes=pipeline.nodes,
                        inference=self.inference)
