import logging
from batch_feature_pipeline import run

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    run()