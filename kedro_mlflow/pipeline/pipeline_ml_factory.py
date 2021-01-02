from pathlib import Path
from typing import Any, Dict, Optional, Union

from kedro.pipeline import Pipeline
from mlflow.models import ModelSignature

from kedro_mlflow.pipeline.pipeline_ml import PipelineML


def pipeline_ml_factory(
    training: Pipeline,
    inference: Pipeline,
    input_name: str = None,
    conda_env: Optional[Union[str, Path, Dict[str, Any]]] = None,
    model_name: Optional[str] = "model",
    model_signature: Union[ModelSignature, str, None] = "auto",
    **kwargs
) -> PipelineML:
    """This function is a helper to create `PipelineML`
    object directly from two Kedro `Pipelines` (one of
    training and one of inference) .

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
        model_signature (Union[ModelSignature, bool]): The mlflow
            signature of the input dataframe common to training
            and inference.
                - If 'auto', it is infered automatically
                - If None, no signature is used
                - if a `ModelSignature` instance, passed
                to the underlying dataframe
        kwargs:
            extra arguments to be passed to `KedroPipelineModel`
            when the PipelineML object is automatically saved at the end of a run.
            This includes:
                - `copy_mode`: the copy_mode to be used for underlying dataset
                when loaded in memory
                - `runner`: the kedro runner to run the model with

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
        model_signature=model_signature,
        **kwargs
    )
    return pipeline
