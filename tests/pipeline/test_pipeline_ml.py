import pytest
from kedro.extras.datasets.pandas import CSVDataSet
from kedro.io import DataCatalog, MemoryDataSet
from kedro.pipeline import Pipeline, node

from kedro_mlflow.pipeline import pipeline_ml_factory
from kedro_mlflow.pipeline.pipeline_ml import KedroMlflowPipelineMLError, PipelineML


def preprocess_fun(data):
    return data


def fit_encoder_fun(data):
    return 4


def apply_encoder_fun(encoder, data):
    return data * encoder


def train_fun(data):
    return 2


def train_fun_hyperparam(data, hyperparam):
    return 2


def predict_fun(model, data):
    return data * model


def predict_fun_with_metric(model, data):
    return data * model, "super_metric"


def predict_fun_return_nothing(model, data):
    pass


def remove_stopwords(data, stopwords):
    return data


def convert_probs_to_pred(data, threshold):
    return data > threshold


@pytest.fixture
def pipeline_with_tag():

    pipeline_with_tag = Pipeline(
        [
            node(
                func=preprocess_fun,
                inputs="raw_data",
                outputs="data",
                tags=["preprocessing"],
            ),
            node(func=train_fun, inputs="data", outputs="model", tags=["training"]),
        ]
    )
    return pipeline_with_tag


@pytest.fixture
def pipeline_ml_with_tag(pipeline_with_tag):
    pipeline_ml_with_tag = pipeline_ml_factory(
        training=pipeline_with_tag,
        inference=Pipeline(
            [node(func=predict_fun, inputs=["model", "data"], outputs="predictions")]
        ),
        input_name="data",
    )
    return pipeline_ml_with_tag


@pytest.fixture
def pipeline_ml_with_intermediary_artifacts():
    full_pipeline = Pipeline(
        [
            node(
                func=preprocess_fun,
                inputs="raw_data",
                outputs="data",
                tags=["training", "preprocessing"],
            ),
            node(
                func=fit_encoder_fun,
                inputs="data",
                outputs="encoder",
                tags=["training"],
            ),
            node(
                func=apply_encoder_fun,
                inputs=["encoder", "data"],
                outputs="encoded_data",
                tags=["training", "inference"],
            ),
            node(
                func=train_fun,
                inputs="encoded_data",
                outputs="model",
                tags=["training"],
            ),
            node(
                func=predict_fun,
                inputs=["model", "encoded_data"],
                outputs="predictions",
                tags=["inference"],
            ),
        ]
    )
    pipeline_ml_with_intermediary_artifacts = pipeline_ml_factory(
        training=full_pipeline.only_nodes_with_tags("training"),
        inference=full_pipeline.only_nodes_with_tags("inference"),
        input_name="data",
    )
    return pipeline_ml_with_intermediary_artifacts


@pytest.fixture
def pipeline_ml_with_inputs_artifacts():
    full_pipeline = Pipeline(
        [
            node(
                func=remove_stopwords,
                inputs=dict(data="data", stopwords="stopwords_from_nltk"),
                outputs="cleaned_data",
                tags=["training", "inference"],
            ),
            node(
                func=train_fun,
                inputs="cleaned_data",
                outputs="model",
                tags=["training"],
            ),
            node(
                func=predict_fun,
                inputs=["model", "cleaned_data"],
                outputs="predictions",
                tags=["inference"],
            ),
        ]
    )
    pipeline_ml_with_inputs_artifacts = pipeline_ml_factory(
        training=full_pipeline.only_nodes_with_tags("training"),
        inference=full_pipeline.only_nodes_with_tags("inference"),
        input_name="data",
    )
    return pipeline_ml_with_inputs_artifacts


@pytest.fixture
def pipeline_ml_with_parameters():
    full_pipeline = Pipeline(
        [
            # almost the same that previsously but stopwords are parameters
            # this is a shared parameter between inference and training22
            node(
                func=remove_stopwords,
                inputs=dict(data="data", stopwords="params:stopwords"),
                outputs="cleaned_data",
                tags=["training", "inference"],
            ),
            # parameters in training pipeline, should not be persisted
            node(
                func=train_fun_hyperparam,
                inputs=["cleaned_data", "params:penalty"],
                outputs="model",
                tags=["training"],
            ),
            node(
                func=predict_fun,
                inputs=["model", "cleaned_data"],
                outputs="predicted_probs",
                tags=["inference"],
            ),
            # this time, there is a parameter only for the inference pipeline
            node(
                func=convert_probs_to_pred,
                inputs=["predicted_probs", "params:threshold"],
                outputs="predictions",
                tags=["inference"],
            ),
        ]
    )
    pipeline_ml_with_parameters = pipeline_ml_factory(
        training=full_pipeline.only_nodes_with_tags("training"),
        inference=full_pipeline.only_nodes_with_tags("inference"),
        input_name="data",
    )
    return pipeline_ml_with_parameters


@pytest.fixture
def dummy_catalog():
    dummy_catalog = DataCatalog(
        {
            "raw_data": MemoryDataSet(),
            "data": MemoryDataSet(),
            "model": CSVDataSet("fake/path/to/model.csv"),
        }
    )
    return dummy_catalog


@pytest.fixture
def catalog_with_encoder():
    catalog_with_encoder = DataCatalog(
        {
            "raw_data": MemoryDataSet(),
            "data": MemoryDataSet(),
            "encoder": CSVDataSet("fake/path/to/encoder.csv"),
            "model": CSVDataSet("fake/path/to/model.csv"),
        }
    )
    return catalog_with_encoder


@pytest.fixture
def catalog_with_stopwords():
    catalog_with_stopwords = DataCatalog(
        {
            "data": MemoryDataSet(),
            "cleaned_data": MemoryDataSet(),
            "stopwords_from_nltk": CSVDataSet("fake/path/to/stopwords.csv"),
            "model": CSVDataSet("fake/path/to/model.csv"),
        }
    )
    return catalog_with_stopwords


@pytest.fixture
def catalog_with_parameters():
    catalog_with_parameters = DataCatalog(
        {
            "data": MemoryDataSet(),
            "cleaned_data": MemoryDataSet(),
            "params:stopwords": MemoryDataSet(["Hello", "Hi"]),
            "params:penalty": MemoryDataSet(0.1),
            "model": CSVDataSet("fake/path/to/model.csv"),
            "params:threshold": MemoryDataSet(0.5),
        }
    )
    return catalog_with_parameters


@pytest.mark.parametrize(
    "tags,from_nodes,to_nodes,node_names,from_inputs",
    [
        (None, None, None, None, None),
        (["training"], None, None, None, None),
        (None, ["train_fun([data]) -> [model]"], None, None, None),
        (None, ["preprocess_fun([raw_data]) -> [data]"], None, None, None),
        (None, None, ["train_fun([data]) -> [model]"], None, None),
        (None, None, None, ["train_fun([data]) -> [model]"], None),
        (None, None, None, None, ["data"]),
    ],
)
def test_filtering_pipeline_ml(
    mocker,
    pipeline_with_tag,
    pipeline_ml_with_tag,
    tags,
    from_nodes,
    to_nodes,
    node_names,
    from_inputs,
):
    """When the pipeline is filtered by the context (e.g calling only_nodes_with_tags,
    from_inputs...), it must return a PipelineML instance with unmodified inference.
    We loop dynamically on the arguments of the function in case of kedro
    modify the filters.
    """

    # pipeline_with_tag, pipeline_ml_with_tag are fixture in conftest

    # remember : the arguments are iterable, so do not pass string directly (e.g ["training"] rather than training)
    filtered_pipeline = pipeline_with_tag.filter(
        tags=tags,
        from_nodes=from_nodes,
        to_nodes=to_nodes,
        node_names=node_names,
        from_inputs=from_inputs,
    )

    filtered_pipeline_ml = pipeline_ml_with_tag.filter(
        tags=tags,
        from_nodes=from_nodes,
        to_nodes=to_nodes,
        node_names=node_names,
        from_inputs=from_inputs,
    )

    # PipelineML class must be preserved when filtering
    # inference should be unmodified
    # training pipeline nodes must be identical to kedro filtering.
    assert isinstance(filtered_pipeline_ml, PipelineML)
    assert filtered_pipeline_ml.inference == pipeline_ml_with_tag.inference
    assert filtered_pipeline.nodes == filtered_pipeline_ml.nodes


@pytest.mark.parametrize(
    "pipeline_ml_obj",
    [
        pytest.lazy_fixture("pipeline_ml_with_tag"),
        pytest.lazy_fixture("pipeline_ml_with_intermediary_artifacts"),
    ],
)
@pytest.mark.parametrize(
    "tags,from_nodes,to_nodes,node_names,from_inputs",
    [
        (["preprocessing"], None, None, None, None),
        (None, None, ["preprocess_fun([raw_data]) -> [data]"], None, None),
        (None, None, None, ["preprocess_fun([raw_data]) -> [data]"], None),
    ],
)
def test_filtering_generate_invalid_pipeline_ml(
    mocker,
    pipeline_ml_obj,
    tags,
    from_nodes,
    to_nodes,
    node_names,
    from_inputs,
):
    """When a PipelineML is filtered it must keep one degree of freedom.
    If by chance a new pipeline with one degree of freedom
    but not the same than previously is generated, it should be catched.
    """
    # remember : the arguments are iterable, so do not pass string directly (e.g ["training"] rather than training)
    with pytest.raises(
        KedroMlflowPipelineMLError,
        match="No free input is allowed",
    ):
        pipeline_ml_obj.filter(
            tags=tags,
            from_nodes=from_nodes,
            to_nodes=to_nodes,
            node_names=node_names,
            from_inputs=from_inputs,
        )


# def test_pipeline_ml_preserve_tags():
#     pass


def test_too_many_free_inputs():
    with pytest.raises(KedroMlflowPipelineMLError, match="No free input is allowed"):
        pipeline_ml_factory(
            training=Pipeline(
                [
                    node(
                        func=preprocess_fun,
                        inputs="raw_data",
                        outputs="neither_data_nor_model",
                    )
                ]
            ),
            inference=Pipeline(
                [
                    node(
                        func=predict_fun,
                        inputs=["model", "data"],
                        outputs="predictions",
                    )
                ]
            ),
            input_name="data",
        )


def test_tagging(pipeline_ml_with_tag):
    new_pl = pipeline_ml_with_tag.tag(["hello"])
    assert all(["hello" in node.tags for node in new_pl.nodes])


def test_invalid_input_name(pipeline_ml_with_tag):
    with pytest.raises(
        KedroMlflowPipelineMLError,
        match="input_name='whoops_bad_name' but it must be an input of 'inference'",
    ):
        pipeline_ml_with_tag.input_name = "whoops_bad_name"


def test_too_many_inference_outputs():
    with pytest.raises(
        KedroMlflowPipelineMLError,
        match="The inference pipeline must have one and only one output",
    ):
        pipeline_ml_factory(
            training=Pipeline(
                [
                    node(
                        func=train_fun,
                        inputs="data",
                        outputs="model",
                    )
                ]
            ),
            inference=Pipeline(
                [
                    node(
                        func=predict_fun_with_metric,
                        inputs=["model", "data"],
                        outputs=["predictions", "metric"],
                    )
                ]
            ),
            input_name="data",
        )


def test_not_enough_inference_outputs():
    with pytest.raises(
        KedroMlflowPipelineMLError,
        match="The inference pipeline must have one and only one output",
    ):
        pipeline_ml_factory(
            training=Pipeline(
                [
                    node(
                        func=train_fun,
                        inputs="data",
                        outputs="model",
                    )
                ]
            ),
            inference=Pipeline(
                [
                    node(
                        func=predict_fun_return_nothing,
                        inputs=["model", "data"],
                        outputs=None,
                    )
                ]
            ),
            input_name="data",
        )
