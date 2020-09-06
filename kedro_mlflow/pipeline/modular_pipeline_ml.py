from pathlib import Path
from typing import Any, Dict, Optional, Union

from kedro.pipeline import Pipeline

from kedro_mlflow.pipeline.pipeline_ml import PipelineML


def pipeline_ml(
    training: Pipeline,
    inference: Pipeline,
    input_name: str = None,
    conda_env: Optional[Union[str, Path, Dict[str, Any]]] = None,
    model_name: Optional[str] = "model",
) -> PipelineML:
    """[summary]

    Args:
        training (Pipeline): The `Pipeline` object that creates
            all mlflow artifacts for prediction (the model,
            but also encoders, binarizers, tokenizers...).
            These artifacts must be persisted in the catalog.yml.
        inference (Pipeline): A `Pipeline` object which will be
            stored in mlflow and use the output(s)
            of the training pipeline (namely, the model)
            to predict the outcome.
        input_name (str, optional): The name of the dataset in
            the catalog.yml which the model's user must provide
            for prediction (i.e. the data). Defaults to None.
        conda_env (Union[str, Path, Dict[str, Any]], optional):
            The minimal conda environment necessary for the
            inference `Pipeline`. It can be either :
                - a path to a "requirements.txt": In this case
                    the packages are parsed and a conda env with
                    your current python_version and these
                    dependencies is returned.
                - a path to an "environment.yml" : the file is
                    uploaded "as is".
                - a Dict : used as the environment
                - None: a base conda environment with your
                    current python version and your project
                    version at training time.
            Defaults to None.
        model_name (Union[str, None], optional): The name of
            the folder where the model will be stored in
            remote mlflow. Defaults to "model".

    Returns:
        PipelineML: A `PipelineML` which is automatically
            discovered by the `MlflowPipelineHook` and
            contains all the information for logging the
            inference pipeline as a Mlflow Model.
    """

    pipeline = PipelineML(
        nodes=training.nodes,
        inference=inference,
        input_name=input_name,
        conda_env=conda_env,
        model_name=model_name,
    )
    return pipeline
