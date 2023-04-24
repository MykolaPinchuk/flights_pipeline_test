### In this repo I am experimenting with building end-to-end ML pipelines

I try to implement ML pipeline for flight delays, following the series of articles:
https://aiinpractice.com/gcp-mlops-vertex-ai-feature-store/

The first part is fine and is implemented in the 'pipeline_flights' notebook. When building the second part, I first tried to do evth in the notebook, but then gave up. Thus the structure of this repo is messy. 

Currently am trying to implement part2 pipeline following original code architecture. Here have to be careful with resource utilization, since it may end up expensive. Over the last 24 hr when I was actively building these projects, my GCP account got billed for almost $20 and I do not yet understand well the cost structure.
Treat FeatureStore like a VM: keep it on only when needed.

It probably means no featurestore for personal projects.
Will probbaly use Dataflow for data preprocessing for training and predictions.
DataFlow cannot scale down to zero for streaming jobs.
But it can use the smallest machines. f1-micro is $5 per month. e2-micro is $7 per month.
So the way to go is to ignore FeatureStore and use Dataflow pipeline for feature preprocessing.



