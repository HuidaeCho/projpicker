# vim: filetype=python tabstop=4 shiftwidth=4 expandtab smarttab autoindent
import arcpy
import os
import sys
from pathlib import Path
import tkinter as tk
from collections import OrderedDict

import projpicker as ppik



################################################################################
# Tkinter GUI
sys.argv += [str(Path(__file__))]


def popup(crs):
    options = {}
    area = {}
    for entry in crs:
        options[entry.get('crs_code')] = entry.get('crs_auth_name')
        area[entry.get('crs_code')] = entry.get('area_sqkm')

    area_s = sorted(options.keys(), key=lambda k: options[k])
    options_s = {}
    for entry in area_s:
        options_s[entry] = f"{options.get(entry)}:{entry}"

    codes = [i for i in options.keys()]
    first = entry[0]
    window = tk.Tk()
    listbox = tk.Listbox(window)
    listbox.pack(side = tk.LEFT, fill = tk.BOTH)
    scrollbar = tk.Scrollbar(window)
    scrollbar.pack(side = tk.RIGHT, fill = tk.BOTH)
    for values in options_s.values():
        listbox.insert(tk.END, values)

    listbox.config(yscrollcommand = scrollbar.set)
    scrollbar.config(command = listbox.yview)

    def selected_item():
        global sel_crs

        for i in listbox.curselection():
            sel_code = listbox.get(i)
            sel_auth = options.get(sel_code)
            sel_crs = sel_code
            window.destroy()

    btn = tk.Button(window, text='OK', command=selected_item)
    btn.pack(side='bottom')
    listbox.pack()

    window.mainloop()
    arcpy.AddMessage(sel_crs)

################################################################################
# ArcGIS Pro Toolbox
class Toolbox(object):
    def __init__(self):
        '''Define the toolbox (the name of the toolbox is the name of the
        .pyt file).'''
        self.label = 'ProjPicker'
        self.alias = 'ProjPicker'

        # List of tool classes associated with this toolbox
        self.tools = [CreateGeometry]


class CreateGeometry(object):
    def __init__(self):
        '''Define the tool (tool name is the name of the class).'''
        self.label = 'ProjPicker Create Geometry'
        self.description = 'ProjPicker wrapper to create geometry shapefile'
        self.canRunInBackground = False

    def getParameterInfo(self):
        '''Define parameter definitions'''
        feature = arcpy.Parameter(
                displayName='Spatial Query',
                name='Spatial query',
                datatype='GPFeatureRecordSetLayer',
                parameterType='required',
                direction='Input')

        new_feat = arcpy.Parameter(
                displayName='Out feature',
                name='Feature',
                datatype='DEFeatureClass',
                parameterType='Required',
                direction='Output')
        geom_type = arcpy.Parameter(
                displayName='Geometry type',
                name='geom_type',
                datatype='DEFeatureClass',
                parameterType='Required',
                direction='Output')

        params = [feature, new_feat, geom_type]
        return params

    def isLicensed(self):
        '''Set whether tool is licensed to execute.'''
        return True

    def updateParameters(self, parameters):
        '''Modify the values and properties of parameters before internal
        validation is performed.
        This method is called whenever a parameter
        has been changed.'''
        return

    def updateMessages(self, parameters):
        '''Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation.'''
        return

    def execute(self, parameters, messages):
        '''The source code of the tool.'''
        # Add path for add current path for tkinter to run
        sys.argv += [os.path.abspath(__file__)]

        args = parameters
        feature = parameters[0]
        desc = arcpy.Describe(feature)
        feature_dir = desc.path
        bbox = desc.extent.projectAs(arcpy.SpatialReference(4326))

        b = bbox.YMin
        t = bbox.YMax
        l = bbox.XMin
        r = bbox.XMax

        arcpy.AddMessage([b, l, t, r])
        if desc.shapeType == "Point":
            crs = ppik.listify_bbox(ppik.query_points([[b, l]]))
        else:
            crs = ppik.listify_bbox(ppik.query_bboxes([[l, t, l, r]]))


        test = popup(crs)

        print('Done!')

        return
