import os
import sys, os
import unittest
import json
import argparse

# set basepath to parent dir for np imports
basePath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(basePath)

# Import custom modules
from np.lib import dataset_store
from np.lib import metric
from np.lib import network


# Run Scenario
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Run NetworkPlanner Scenario")
    parser.add_argument('metric_model_name', choices=metric.getModelNames(),
                        help="metric model definition to run")
    parser.add_argument('metric_model_params', type=argparse.FileType('r'),
                        help="model parameters json file")
    parser.add_argument('network_model_name', choices=network.getModelNames(),
                        help="network model definition to run")
    parser.add_argument('network_model_params', type=argparse.FileType('r'),
                        help="model parameters json file")
    parser.add_argument('output_path', help="directory where outputs will be placed")
    parser.add_argument('input_nodes_file', help="csv file of nodes (lat,lon,population,...)")
                       
    args = parser.parse_args()

    # make output dir if not exists
    outputDataPath = args.output_path
    if not os.path.exists(outputDataPath):
        os.makedirs(outputDataPath)

    targetPath = os.path.join(outputDataPath, "dataset.db")
    datasetStore = dataset_store.create(targetPath, args.input_nodes_file)

    # setup models
    metricModel = metric.getModel(args.metric_model_name)
    metricConfiguration = json.load(args.metric_model_params)
    networkModel = network.getModel(args.network_model_name)
    networkConfiguration = json.load(args.network_model_params)

    # Run metric model
    metricValueByOptionBySection = datasetStore.applyMetric(metricModel, metricConfiguration)

    # Now that metrics (mvMax in particular) have been calculated
    # we can build the network
    networkValueByOptionBySection = datasetStore.buildNetwork(networkModel, networkConfiguration, writeJobLog=False)

    # Now that the network's been built (and the electrification option 
    # is chosen) run the aggregate calculations
    metricValueByOptionBySection = datasetStore.updateMetric(metricModel, metricValueByOptionBySection)

    metric.saveMetricsConfigurationCSV(os.path.join(outputDataPath, 'metrics-job-input'), metricConfiguration)
    metric.saveMetricsCSV(os.path.join(outputDataPath, 'metrics-global'), metricModel, metricValueByOptionBySection)
    datasetStore.saveMetricsCSV(os.path.join(outputDataPath, 'metrics-local'), metricModel)
    datasetStore.saveSegmentsSHP(os.path.join(outputDataPath, 'networks-proposed'), is_existing=False)

