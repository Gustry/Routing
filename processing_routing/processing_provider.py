# -*- coding: utf-8 -*-
from processing.core.AlgorithmProvider import AlgorithmProvider

from Routing.processing_routing.routing_two_points import RoutingTwoPointsGeoAlgorithm
from Routing.processing_routing.allocating_exits import AllocatingExitsGeoAlgorithm
from Routing.processing_routing.DeleteHoles import DeleteHoles
from Routing.processing_routing.LinesIntersection import LinesIntersection
from Routing.processing_routing.SnapPointsProject import SnapPointsProject
from Routing.processing_routing.SplitLinesWithPoints import SplitLinesWithPoints

class ProcessingProvider(AlgorithmProvider):

    def __init__(self):
        AlgorithmProvider.__init__(self)

        self.activate = True

        # Load algorithms
        self.alglist = [AllocatingExitsGeoAlgorithm(),
                        DeleteHoles(),
                        LinesIntersection(),
                        SnapPointsProject(),
                        SplitLinesWithPoints(),
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

