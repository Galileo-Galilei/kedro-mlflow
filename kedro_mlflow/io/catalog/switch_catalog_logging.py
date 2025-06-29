def switch_catalog_logging(catalog, logging_flag=True):
    for name, dataset in catalog.items():
        if type(dataset).__name__.startswith("Mlflow"):
            catalog[name]._logging_activated = logging_flag
