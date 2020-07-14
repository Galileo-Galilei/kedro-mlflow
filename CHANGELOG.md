# 0.1.0
## Major features and improvements
- Add cli ``kedro mlflow init`` to udpdate the template and ``kedro mlflow ui`` to open ``mlflow`` user interface with your project configuration
- Add hooks ``MlflowNodeHook`` and ``MlflowPipelineHook`` for parameters autologging and model autologging
- Add ``MlflowDataSet`` for artifacts autologging
- Add ``PipelineMl`` class and its ``pipeline_ml`` factory for pipeline packaging and service
