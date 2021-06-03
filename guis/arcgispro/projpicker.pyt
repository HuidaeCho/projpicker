# vim: filetype=python tabstop=4 shiftwidth=4 expandtab smarttab autoindent
import arcpy
import os
import sys
from pathlib import Path
import tkinter as tk
from collections import OrderedDict
import json
import requests
import shutil
import projpicker as ppik

################################################################################
# Constants

WGS84 = 4326

# Assign for global variable
sel_crs = "EPSG:4326"


################################################################################
# Tkinter GUI

# Add path for add current path for tkinter to run
sys.argv += [str(Path(__file__))]


def popup(crs):
    """
    Tkinter GUI for selecting new CRS

    Args:
        crs (list): Queryied CRS information from projpicker
    """

    # Create CRS info and area dicts
    options = {}
    area = {}
    for entry in crs:
        # Create main info dict queryable by code
        options[entry.get('crs_code')] = entry
        # Create area dict for easy sorting
        area[entry.get('crs_code')] = entry.get('area_sqkm')

    # Sort by area to get most localized proj
    area_s = sorted(area.keys(), key=lambda k: area[k])
    # Sort options dict by area
    options_s = {}
    for entry in area_s:
        options_s[entry] = f"{options.get(entry).get('crs_auth_name')}:{entry}"

    # Main window
    window = tk.Tk()
    window.geometry("900x400")
    window.title("ProjPicker Geometry Creation (ArcGIS Pro)")

    # Text for CRS Info
    T = tk.Text(window, height = 5, width = 40)
    T.pack(side=tk.RIGHT, fill=tk.BOTH)
    T.insert(tk.END, "Use 'CRS Info' to show projection info")

    # List of crs
    listbox = tk.Listbox(window)
    listbox.pack(side = tk.LEFT, fill = tk.BOTH, expand=False)

    # Add scrollbar for list
    scrollbar = tk.Scrollbar(window)
    scrollbar.pack(side = tk.LEFT, fill = tk.BOTH)

    # Populate list
    for values in options_s.values():
        listbox.insert(tk.END, values)

    # Add widgets
    listbox.config(yscrollcommand = scrollbar.set)
    scrollbar.config(command = listbox.yview)

    # Retrieve selected CRS from List
    def selected_item():
        global sel_crs
        for i in listbox.curselection():

            # get auth:code string
            sel_code = listbox.get(i)
            # get just code
            sel_auth = options.get(sel_code.split(":")[1])
            # update sel_crs
            sel_crs = sel_code
            # Close window
            window.destroy()

    # Show CRS info in right panel
    def get_info():
        for i in listbox.curselection():
            # get auth:code string
            sel_code = listbox.get(i)
            # get full ppik return json
            sel_auth = options.get(sel_code.split(":")[1])
            # format json
            pp = json.dumps(sel_auth, indent=2, sort_keys=True)
            # delete previous text
            T.delete('1.0', tk.END)
            # insert new text
            T.insert(tk.END, pp)

    # Buttons
    btn = tk.Button(window, text='OK', command=selected_item)
    btn.pack(side=tk.LEFT)
    btn1 = tk.Button(window, text="CRS Info", command=get_info)
    btn1.pack(side=tk.RIGHT)

    # insert list into window
    listbox.pack()

    # run gui
    window.mainloop()

    # return selected CRS
    return sel_crs


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
                displayName='Out Feature',
                name='Feature',
                datatype='DEFeatureClass',
                parameterType='Required',
                direction='Output')

        geom_type = arcpy.Parameter(
                displayName='Geometry Type',
                name='geom_type',
                datatype='GPString',
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

        # Read parameters
        feature = parameters[0]
        new_feat = parameters[1]
        geom_type = parameters[2]

        # Get path of spatial query feature
        desc = arcpy.Describe(feature)
        feature_dir = desc.path

        # get extent in lat lon
        bbox = desc.extent.projectAs(arcpy.SpatialReference(WGS84))

        b = bbox.YMin
        t = bbox.YMax
        l = bbox.XMin
        r = bbox.XMax

        arcpy.AddMessage(f"Querying CRS's within {[b, t, l, r]}")

        # If querying shape is a point then query by point
        # else use bounding box
        if desc.shapeType == "Point":
            crs = ppik.listify_bbox(ppik.query_points([[b, l]]))
        else:
            crs = ppik.listify_bbox(ppik.query_bboxes([[b, t, l, r]]))

        # Run GUI and return the selected CRS
        sel_crs = popup(crs)

        # Get file path of output geometry
        desc = arcpy.Describe(new_feat)
        out_dir = desc.path
        out_file = desc.name

        # Create spatial reference object
        # MUST be integer so IGNF authority codes will not work
        spat_ref = arcpy.SpatialReference(int(sel_crs.split(':')[1]))

        # Create output geometry
        arcpy.management.CreateFeatureclass(out_dir, out_file,
                spatial_reference=spat_ref)

        return

