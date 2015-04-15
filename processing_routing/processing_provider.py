# -*- coding: utf-8 -*-
from processing.core.AlgorithmProvider import AlgorithmProvider

from Routing.processing_routing.routable_layer import RoutableLayerGeoAlgorithm
from Routing.processing_routing.routing_two_points import RoutingTwoPointsGeoAlgorithm

class ProcessingProvider(AlgorithmProvider):

    def __init__(self):
        AlgorithmProvider.__init__(self)

        self.activate = True

        # Load algorithms
        self.alglist = [RoutableLayerGeoAlgorithm(),
                        RoutingTwoPointsGeoAlgorithm()]

        for alg in self.alglist:
            alg.provider = self

    def initializeSettings(self):
        AlgorithmProvider.initializeSettings(self)

    def unload(self):
        AlgorithmProvider.unload(self)

    def getName(self):
        return 'Routing'

    def getDescription(self):
        return 'Routing'

    def _loadAlgorithms(self):
        self.algs = self.alglist

    def getSupportedOutputTableExtensions(self):
        return ['csv']

