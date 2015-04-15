# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Routing
                                 A QGIS plugin
 Routing
                              -------------------
        begin                : 2015-04-08
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Kartoza
        email                : etienne@kartoza.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from processing.core.Processing import Processing
from processing_routing.processing_provider import ProcessingProvider


class Routing:

    def __init__(self):

        self.provider = ProcessingProvider()
        Processing.addProvider(self.provider, True)

    def initGui(self):
        pass

    def unload(self):
        Processing.removeProvider(self.provider)
