# ``Hooks``

This package provides 2 new hooks.

## ``MlflowPipelineHook``

This hook :

  1. manages mlflow settings at the beginning and the end of the run (run start / end).
  2. log useful informations for reproducibility as ``mlflow tags`` (including kedro ``Journal`` information and the commands used to launch the run).
  3. register the pipeline as a valid ``mlflow model`` if [it is a ``PipelineML`` instance](#new-pipeline)

## ``MlflowNodeHook``

This hook:

  1. must be used with the ``MlflowPipelineHook``
  2. autolog nodes parameters each time the pipeline is run (with ``kedro run`` or programatically).
