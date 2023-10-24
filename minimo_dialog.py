# -*- coding: utf-8 -*-
"""
/***************************************************************************
 minimoDialog
                                 A QGIS plugin
 minimo
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2023-07-04
        git sha              : $Format:%H$
        copyright            : (C) 2023 by a
        email                : b
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

import os

from qgis.PyQt.QtCore import QVariant
from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.gui import QgsMessageBar
from qgis.core import QgsMapLayerProxyModel
from qgis.core import (
    QgsMessageLog,
    Qgis,
    QgsApplication,
    QgsDataSourceUri,
    QgsCategorizedSymbolRenderer,
    QgsClassificationRange,
    QgsPointXY,
    QgsProject,
    QgsExpression,
    QgsField,
    QgsFields,
    QgsFeature,
    QgsFeatureRequest,
    QgsFeatureRenderer,
    QgsGeometry,
    QgsGraduatedSymbolRenderer,
    QgsMarkerSymbol,
    QgsMessageLog,
    QgsRectangle,
    QgsRendererCategory,
    QgsRendererRange,
    QgsSymbol,
    QgsVectorDataProvider,
    QgsVectorLayer,
    QgsVectorFileWriter,
    QgsWkbTypes,
    QgsSpatialIndex,
    QgsVectorLayerUtils
)


# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'minimo_dialog_base.ui'))


class minimoDialog(QtWidgets.QDialog, FORM_CLASS):

    def __init__(self, _iface):
        """Constructor."""
        super(minimoDialog, self).__init__(None) #parent = None
        self.iface = _iface

        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect

        self.setupUi(self)
        self.combo_DEM.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.combo_metodos.addItems(["Kirpich", "California Culverts practice", "Federal aviation agency", "UDFCD Denver CO"])

        #self.widget_dir.fileChanged.connect(dir_path = self.widget_dir.filePath())
        self.btn1.clicked.connect(self.hola_mundo)
        self.btn_generar_estructura.clicked.connect(self.generar_estructura)
        self.btn_calcular_atributos.clicked.connect(self.calcular_atributos)

    def hola_mundo(self):
        #self.iface.messageBar().pushMessage("Exito",self.widget_dir.filePath() , level = Qgis.Success, duration=5)
        #self.iface.messageBar().pushMessage("Exito","El programa esta funcionando correctamente", level = Qgis.Success, duration=5)
        #self.iface.messageBar().pushMessage(f"Capa seleccionada:",f"{self.combo_DEM.currentLayer()}", level = Qgis.Success, duration=5)
        #print(self.combo_DEM.currentLayer())
        print(f"Metodo seleccionado: {self.combo_metodos.currentText()} indice: {self.combo_metodos.currentIndex()}")

    def generar_estructura(self):
        dir_path = self.widget_dir.filePath()
        self.create_lluvias_layer(dir_path)
        self.create_uniones_layer(dir_path)
        self.create_canales_layer(dir_path)
        self.create_subcuencas_layer(dir_path)
        self.create_lineas_de_escurrimiento_layer(dir_path)

    def calcular_atributos(self):
        self.calculate_canales_attributes(self.combo_DEM.currentLayer())
        self.calculate_escurrimiento_attributes(self.combo_DEM.currentLayer())
        self.calculate_subcuencas_attributes()
        self.calculate_subcuencas_tc(self.combo_metodos.currentText())

    def create_add_layer(self, layer_name, layer_path, layer_fields, layer_type, driver):
        save_options = QgsVectorFileWriter.SaveVectorOptions()
        save_options.driverName = driver
        writer = QgsVectorFileWriter.create(
            layer_path,
            layer_fields,
            layer_type,
            QgsProject.instance().crs(),                #crs del proyecto
            QgsProject.instance().transformContext(),   #transform context?
            save_options     #opciones de guardado
            )
        if writer.hasError() != QgsVectorFileWriter.NoError:
            self.iface.messageBar().pushMessage("Error:", f"Fail when creating {layer_path}!: {writer.errorMessage()}", level=Qgis.Error)
        del writer  # borro el writer para guardar los cambios en el disco
        layer = self.iface.addVectorLayer(layer_path, layer_name, "ogr")    #agrego la capa al proyecto
        if not layer:
            self.iface.messageBar().pushMessage("Error:", f"Failed to load {layer_name}!", level=Qgis.Error)

    #   Esta funcion recibe como parametro la ruta donde se va a guardar la capa, crea los atributos de la capa
    #   subcuenca y llama a la funcion create_add_layer() para guardarla en la ubicacion recibida como parametro.
    def create_subcuencas_layer(self, dir_path):    
        save_path = dir_path + "/subcuencas.gpkg" #ruta donde se va a guardar la capa
        fields = QgsFields()    #defino los atributos de la capa
        fields.append(QgsField("Identificador", QVariant.String))
        fields.append(QgsField("Area", QVariant.Double))
        fields.append(QgsField("C", QVariant.Double))
        fields.append(QgsField("Tc", QVariant.Double))
        fields.append(QgsField("Linea de escurrimiento", QVariant.String))
        fields.append(QgsField("Aguas abajo", QVariant.String))
        
        self.create_add_layer("Subcuencas",save_path, fields, QgsWkbTypes.Polygon, "gpkg")

    #   Esta funcion recibe como parametro la ruta donde se va a guardar la capa, crea los atributos de la capa
    #   lineas de escurrimiento y llama a la funcion create_add_layer() para guardarla en la ubicacion recibida como parametro.
    def create_lineas_de_escurrimiento_layer(self, dir_path):    
        save_path = dir_path + "/lineas_de_escurrimiento.gpkg" #ruta donde se va a guardar la capa
        fields = QgsFields()    #defino los atributos de la capa
        fields.append(QgsField("Identificador", QVariant.String))
        fields.append(QgsField("Longitud", QVariant.Double))
        fields.append(QgsField("Cota superior", QVariant.Double))
        fields.append(QgsField("Cota inferior", QVariant.Double))
        fields.append(QgsField("S", QVariant.Double))
        
        self.create_add_layer("Lineas de escurrimiento",save_path, fields, QgsWkbTypes.LineString, "gpkg")
    
    #   Esta funcion recibe como parametro la ruta donde se va a guardar la capa, crea los atributos de la capogr csv drivera
    #   canales y llama a la funcion create_add_layer() para guardarla en la ubicacion recibida como parametro.
    def create_canales_layer(self, dir_path):   
        save_path = dir_path + "/canales.gpkg" #ruta donde se va a guardar la capa
        fields = QgsFields()    #defino los atributos de la capa
        fields.append(QgsField("Identificador", QVariant.String))
        fields.append(QgsField("Tipo", QVariant.String))
        fields.append(QgsField("Longitud", QVariant.Double))
        fields.append(QgsField("Cota superior", QVariant.Double))
        fields.append(QgsField("Cota inferior", QVariant.Double))
        fields.append(QgsField("S", QVariant.Double))
        fields.append(QgsField("Aguas abajo", QVariant.String))
        
        self.create_add_layer("Canales",save_path, fields, QgsWkbTypes.LineString, "gpkg")

    #   Esta funcion recibe como parametro la ruta donde se va a guardar la capa, crea los atributos de la capa
    #   uniones y llama a la funcion create_add_layer() para guardarla en la ubicacion recibida como parametro.
    def create_uniones_layer(self, dir_path):   
        save_path = dir_path + "/uniones.gpkg" #ruta donde se va a guardar la capa
        fields = QgsFields()    #defino los atributos de la capa
        fields.append(QgsField("Identificador", QVariant.String))
        fields.append(QgsField("Tipo", QVariant.String))
        fields.append(QgsField("Aguas Abajo", QVariant.String))
        fields.append(QgsField("Alto boca", QVariant.Double))
        fields.append(QgsField("Ancho boca", QVariant.Double))
        fields.append(QgsField("Derivacion subterranea", QVariant.String))

        self.create_add_layer("Uniones",save_path, fields, QgsWkbTypes.Point, "gpkg")

    #   Esta funcion recibe como parametro la ruta donde se va a guardar la capa, crea los atributos de la capa
    #   lluvias y llama a la funcion create_add_layer() para guardarla en la ubicacion recibida como parametro.
    def create_lluvias_layer(self, dir_path):   
        save_path = dir_path + "/lluvias.csv" #ruta donde se va a guardar la capa
        fields = QgsFields()    #defino los atributos de la capa
        fields.append(QgsField("Identificador", QVariant.String))
        fields.append(QgsField("T", QVariant.Double))   #en años
        fields.append(QgsField("i", QVariant.Double))   #intensidad en milimimetos/hora
        fields.append(QgsField("d", QVariant.Int))      #duracion en minutos

        self.create_add_layer("lluvias",save_path, fields, QgsWkbTypes.NoGeometry,"csv")

    #Esta funcion toma un objeto linea y un modelo digital de elevacion y devuelve la altura en el punto inicial y final.
    def calculate_line_levels(self, line, DEM):
        # Obtengo los puntos inicial y final de la linea
        start_point = line.geometry().asPolyline()[0]
        end_point = line.geometry().asPolyline()[-1]
        # Obtengo la altura en el punto dado
        value_s, success_s = DEM.dataProvider().sample(start_point, 1)  # 1 indica que se obtiene el valor de la banda 1 del MDE
        value_e, success_e = DEM.dataProvider().sample(end_point, 1)
        
        if success_s and success_e:
            return value_s, value_e
        else:
            return None, None       #si no existen valores para los puntos inicial y final retorno None

    def calculate_subcuencas_attributes(self):
        layer = QgsProject.instance().mapLayersByName('Subcuencas')[0]
        features = layer.getFeatures(QgsFeatureRequest())
        for f in features:
            #iniciar edicion
            layer.startEditing()
            layer.changeAttributeValue(f.attribute("fid"),f.fieldNameIndex("Area"), f.geometry().area())
            #cerrar edicion
            layer.commitChanges()

    def calculate_line_attributes(self, layer, line, DEM):
        length = line.geometry().length()
        high_level, low_level = self.calculate_line_levels(line, DEM)
        #iniciar edicion
        layer.startEditing()        
        layer.changeAttributeValue(line.attribute("fid"),line.fieldNameIndex("Longitud"), length)
        if low_level != None and high_level != None:
            layer.changeAttributeValue(line.attribute("fid"),line.fieldNameIndex("Cota inferior"), low_level)
            layer.changeAttributeValue(line.attribute("fid"),line.fieldNameIndex("Cota superior"), high_level)
            s = (high_level - low_level)/length
            if 0 < s:
                layer.changeAttributeValue(line.attribute("fid"),line.fieldNameIndex("S"), s)
            else:
                self.iface.messageBar().pushMessage("Pendiente negativa:", f'el sentido de "{line.attribute("Identificador")}" debe ser invertido.', level=Qgis.Warning)
        else:
            self.iface.messageBar().pushMessage("Imposible calcular cotas:", f'Uno de los extremos de "{line.attribute("Identificador")}" esta fuera del MDE.', level=Qgis.Warning)
        #cerrar edicion
        layer.commitChanges()

    def calculate_canales_attributes(self, DEM):
        layer = QgsProject.instance().mapLayersByName("Canales")[0]
        features = layer.getFeatures(QgsFeatureRequest())
        for f in features:
            self.calculate_line_attributes(layer, f, DEM)

    def calculate_escurrimiento_attributes(self, DEM):
        layer_lineas = QgsProject.instance().mapLayersByName("Lineas de escurrimiento")[0]
        layer_subcuencas = QgsProject.instance().mapLayersByName('Subcuencas')[0]
        # Validamos que la linea de escurrimiento este dentro de su subcuenca
        for linea in layer_lineas.getFeatures(QgsFeatureRequest()):
            for subcuenca in layer_subcuencas.getFeatures(QgsFeatureRequest()):
                if linea.attribute("Identificador") == subcuenca.attribute("Linea de escurrimiento"):
                    if linea.geometry().within(subcuenca.geometry()):
                        # calculamos sus atributos
                        self.calculate_line_attributes(layer_lineas, linea, DEM)
                    else:
                        self.iface.messageBar().pushMessage("Imposible calcular atributos:", f'la linea de escurrimiento "{linea.attribute("Identificador")}" esta fuera de su subcuenca.', level=Qgis.Warning)
                    break

    def calculate_tc(self, method, L, H, S, C):
        L = L/1000
        print(f'method: {type(method)},L: {type(L)},H: {type(H)},S: {type(S)},C: {type(C)}')
        if method == "Kirpich":
            tc = 3.989*(L**0.77)*(S**-0.385)			# Kirpich
        elif method == "California Culverts practice":
            tc = 57*(L**1.155)*(H**-0.385)			# California Culverts practice
        elif method == "Federal aviation agency":
            tc= 22.73*(1.10-C)*(L**0.50)*(S**-0.33)	# Federal aviation agency
        elif method == "UDFCD Denver CO":
            tc = 0.70*(1.10-C)*(L**0.50)*(S**-0.33)	# UDFCD Denver CO
        return tc
        
    def calculate_subcuencas_tc(self, method):
        layer_lineas = QgsProject.instance().mapLayersByName("Lineas de escurrimiento")[0]
        layer_subcuencas = QgsProject.instance().mapLayersByName('Subcuencas')[0]
        # Validamos que la linea de escurrimiento este dentro de su subcuenca
        for subcuenca in layer_subcuencas.getFeatures(QgsFeatureRequest()):
            for linea in layer_lineas.getFeatures(QgsFeatureRequest()):
                if linea.attribute("Identificador") == subcuenca.attribute("Linea de escurrimiento"):
                    if linea.geometry().within(subcuenca.geometry()) and linea.attribute("S") > 0 :
                        L = linea.attribute("Longitud")
                        S = linea.attribute("S")
                        H = linea.attribute("Cota superior") - linea.attribute("Cota inferior")
                        C = subcuenca.attribute("C")
                        layer_subcuencas.startEditing()
                        layer_subcuencas.changeAttributeValue(subcuenca.attribute("fid"),subcuenca.fieldNameIndex("Tc"),self.calculate_tc(method, L, H, S, C))
                        layer_subcuencas.commitChanges()
                    else:
                        self.iface.messageBar().pushMessage("Imposible calcular Tc:", f'la linea de escurrimiento "{linea.attribute("Identificador")}" es invalida.', level=Qgis.Warning)
                else:
                    self.iface.messageBar().pushMessage("Imposible calcular Tc:", f'no se ha encontrado la linea de escurrimiento para la subcuenca "{subcuenca.attribute("Identificador")}".', level=Qgis.Warning)