# ``kedro-mlflow`` mlops solution

## Reminder

We assume that we want to solve the following challenges among those described in ["Why we need a mlops framework"](./01_why_framework.md) section:

- serve pipelines (which handles business objects) instead of models
- synchronize training and inference by packaging inference pipeline at training time

## Enforcing these principles with a dedicated tool

### Synchronizing training and inference pipeline

To solve the problem of desynchronization between training and inference, ``kedro-mlflow`` offers a `PipelineML` class (which subclasses Kedro `Pipeline` class). A `PipelineML` is simply a Kedro standard ``Pipeline`` (the "training") which has a reference to another ``Pipeline`` (the "inference"). The two pipelines must share a common input DataSet name, which represents the data you will perform operations on (either train on for the training pipeline, or predict on for the inference pipeline).

This class implements several methods to compare the ``DataCatalog``s associated to each of the two binded pipelines and performs subsetting oparations. This makes it quite difficult to handle directly. Fortunately, ``kedro-mlflow`` provides a convenient API to create ``PipelineML`` objects: the ``pipeline_ml_factory`` function.

The use of ``pipeline_ml_factory`` is very straightforward, especially if you have used the [project architecture described previously](./02_ml_project_components.md). The best place to create such an object is your `hooks.py` file which will look like this:

```python
# hooks.py
from kedro_mlflow_tutorial.pipelines.ml_app.pipeline import create_ml_pipeline


class ProjectHooks:
    @hook_impl
    def register_pipelines(self) -> Dict[str, Pipeline]:

        ml_pipeline = create_ml_pipeline()

        # convert your two pipelines to a PipelinML object
        training_pipeline_ml = pipeline_ml_factory(
            training=ml_pipeline.only_nodes_with_tags("training"),
            inference=ml_pipeline.only_nodes_with_tags("inference"),
            input_name="instances",
        )

        return {"__default__": training_pipeline_ml}
```

> So, what? We have created a link between our two pipelines, but the gain is not obvious at first glance. The 2 following sections demonstrates that such a construction enables to package and serve automatically the inference pipeline when executing the training one.

### Packaging and serving a Kedro Pipeline

Mlflow offers the possibility to create [custom model class](https://www.mlflow.org/docs/latest/models.html#custom-python-models). Mlflow offers a variety of tool to package/containerize, deploy and serve such models.

``kedro-mlflow`` has a ``KedroPipelineModel`` class (which inherits from ``mlflow.pyfunc.PythonModel``) which can turn any kedro ``PipelineML`` object to a Mlflow Model.

To convert a ``PipelineML``, you need to declare it as a ``KedroPipelineModel`` and then log it to mlflow:

```python
from pathlib import Path
from kedro.framework.context import load_context
from kedro_mlflow.mlflow import KedroPipelineModel
from mlflow.models import ModelSignature

# pipeline_training is your PipelineML object, created as previsously
catalog = load_context(".").io

# artifacts are all the inputs of the inference pipelines that are persisted in the catalog
artifacts = pipeline_training.extract_pipeline_artifacts(catalog)

# (optional) get the schema of the input dataset
input_data = catalog.load(pipeline_training.input_name)
model_signature = infer_signature(model_input=input_data)

kedro_model = KedroPipelineModel(pipeline=pipeline_training, catalog=catalog)

mlflow.pyfunc.log_model(
    artifact_path="model",
    python_model=kedro_model,
    artifacts=artifacts,
    conda_env={"python": "3.7.0", dependencies: ["kedro==0.16.5"]},
    signature=model_signature,
)
```

Note that you need to provide the ``log_model`` function a bunch of non trivial-to-retrieve informations (the conda environment, the "artifacts" i.e. the persisted data you need to reuse like tokenizers / ml models / encoders, the model signature i.e. the columns names and types...). The ``PipelineML`` object has methods like `extract_pipeline_artifacts` to help you, but it needs some work on your side.

> Saving Kedro pipelines as Mlflow Model objects is convenient and enable pipeline serving serving. However, it does not does not solve the decorrelation between training and inference: each time one triggers a training pipeline, (s)he must think to save it immediately afterwards. Good news: triggering operations at some "execution moment" of a Kedro ``Pipeline`` (like after it finished runnning) is exactly what hooks are designed for!

### kedro-mlflow's magic: inference autologging

When running the training pipeline, we have all the desired informations we want to pass to the ``KedroPipelineModel`` class and ``mlflow.pyfunc.log_model`` function:

- the artifacts exist in the DataCatalog if they are persisted
- the "instances" dataset is loaded at the beginning of training, thus we can infer its schema (columns names and types)
- the inference and training pipeline codes are retrieved at the same moments, so consistency checks can be performed

Hence, ``kedro-mlflow`` provides a ``MlflowHook.after_pipeline_run`` hook which perfoms the following operations:

- check if the pipeline that have ust been run is a ``PipelineML`` object
- in case it is, create the ``KedroPipelineModel`` like above and log it to mlflow

> We have achieved perfect synchronicity since the exact inference pipeline (with code, and artifacts) will be logged in mlflow each time the training pipeline is executed. The model is than accessible in the mlflow UI "artifacts" section and can be downloaded, or [served as an API with the ``mlflow serve`` command](https://www.mlflow.org/docs/latest/cli.html#mlflow-models-serve), or [it can be used in the `catalog.yml` with the `MlflowModelLogger` for further reuse](https://github.com/Galileo-Galilei/kedro-mlflow-tutorial#serve-the-inference-pipeline-to-a-end-user).

### Reuse the model in kedro

Say that you an to reuse this inference model as the input of another kedro pipeline (one of the "user_app" application). ``kedro-mlflow`` provides a ``MlflowModelLoggerDataSet`` class which can be used int the ``catalog.yml`` file:

```yaml
# catalog.yml

pipeline_inference_model:
  type: kedro_mlflow.io.models.MlflowModelLoggerDataSet
  flavor: mlflow.pyfunc
  pyfunc_workflow: python_model
  artifact_path: kedro_mlflow_tutorial  # the name of your mlflow folder = the model_name in pipeline_ml_factory
  run_id: <your-run-id>  
```
