# Pipelines

## ``PipelineML`` and ``pipeline_ml_factory``

``PipelineML`` is a new class which extends ``Pipeline`` and enable to bind two pipelines (one of training, one of inference) together. This class comes with a ``KedroPipelineModel`` class for logging it in mlflow. A pipeline logged as a mlflow model can be served using ``mlflow models serve`` and ``mlflow models predict`` command.  

The ``PipelineML`` class is not intended to be used directly. A ``pipeline_ml_factory`` factory is provided for user friendly interface.

Example within kedro template:

```python
# in src/PYTHON_PACKAGE/pipeline.py

from PYTHON_PACKAGE.pipelines import data_science as ds


def create_pipelines(**kwargs) -> Dict[str, Pipeline]:
    data_science_pipeline = ds.create_pipeline()
    training_pipeline = pipeline_ml_factory(
        training=data_science_pipeline.only_nodes_with_tags(
            "training"
        ),  # or whatever your logic is for filtering
        inference=data_science_pipeline.only_nodes_with_tags("inference"),
    )

    return {
        "ds": data_science_pipeline,
        "training": training_pipeline,
        "__default__": data_engineering_pipeline + data_science_pipeline,
    }
```

Now each time you will run ``kedro run --pipeline=training`` (provided you registered ``MlflowHook`` in you ``run.py``), the full inference pipeline will be registered as a mlflow model (with all the outputs produced by training as artifacts : the machine learning model, but also the *scaler*, *vectorizer*, *imputer*, or whatever object fitted on data you create in ``training`` and that is used in ``inference``).

Note that:

- the `inference` pipeline `input_name` can be a `MemoryDataset` and it belongs to inference pipeline `inputs`
- Apart form `input_name`, all other `inference` pipeline `inputs` must be persisted locally on disk (i.e. it must not be `MemoryDataset` and must have a local `filepath`)
- the `inference` pipeline `inputs` must belong to training `outputs` (vectorizer, binarizer, machine learning model...)
- the `inference` pipeline must have one and only one `output`

```{caution}
``PipelineML`` objects do not implement all filtering methods of a regular ``Pipeline``, and you cannot add or substract 2 ``PipelineML`` together. The rationale is that a filtered ``PipelineML`` is not a ``PipelineML`` in general, because the [filtering is not consistent between training and inference](https://github.com/Galileo-Galilei/kedro-mlflow/issues/554). You can see the ones which are supported [in the code](https://github.com/Galileo-Galilei/kedro-mlflow/blob/master/kedro_mlflow/pipeline/pipeline_ml.py#L162).
```

You can also directly log a ``PipelineML`` object in ``mlflow`` programatically:

```python
from pathlib import Path
from kedro.framework.context import load_context
from kedro_mlflow.mlflow import KedroPipelineModel
from mlflow.models import ModelSignature

# pipeline_training is your PipelineML object, created as previsously
catalog = load_context(".").io

# artifacts are all the inputs of the inference pipelines that are persisted in the catalog
artifacts = pipeline_training.extract_pipeline_artifacts(catalog)

# get the schema of the input dataset
input_data = catalog.load(pipeline_training.input_name)
model_signature = infer_signature(model_input=input_data)

mlflow.pyfunc.log_model(
    artifact_path="model",
    python_model=KedroPipelineModel(pipeline=pipeline_training, catalog=catalog),
    artifacts=artifacts,
    conda_env={"python": "3.10.0", dependencies: ["kedro==0.18.11"]},
    signature=model_signature,
)
```

It is also possible to pass arguments to `KedroPipelineModel` to specify the runner or the copy_mode of ``MemoryDataset`` for the inference ``Pipeline``. This may be faster especially for compiled model (e.g keras, tensorflow...), and more suitable for an API serving pattern. Since ``kedro-mlflow==0.12.0``, ``copy_mode="assign"`` has become the default.

```python
KedroPipelineModel(pipeline=pipeline_training, catalog=catalog, copy_mode="assign")
```

Available `copy_mode` are ``assign``, ``copy`` and ``deepcopy``. It is possible to pass a dictionary to specify different copy mode for each dataset.
