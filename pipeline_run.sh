# may need to create or load venv here
source /opt/conda/bin/activate ~/conda_env/py38

export BUCKET="mpg3-testflights-polished-vault-379315"
export PROJECT_ID="polished-vault-379315"
export REGION="us-central1"
export FEATURE_STORE_ID="662390005506"

python ./main.py \
    --input=gs://${BUCKET}/data/processed/2020/2020-05.csv \
    --output-flights=gs://${BUCKET}/features/flight_features/ \
    --output-airports=gs://${BUCKET}/features/airport_features/ \
    --output-read-instances=gs://${BUCKET}/features/read_instances/ \
    --runner=DataflowRunner \
    --project=${PROJECT_ID} \
    --region=us-central1 \
    --staging_location=gs://${BUCKET}/beam_staging \
    --temp_location=gs://${BUCKET}/beam_tmp \
    --job_name=flight-batch-features 