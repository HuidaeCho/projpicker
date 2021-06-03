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

# Assign default CRS so tool wont fail if selection is closed.
sel_crs = "EPSG:4326"


################################################################################
# Tkinter GUI

# Add path for add current path for tkinter to run
sys.argv = [str(Path(__file__))]


def popup(crs):
    """
    Tkinter GUI for selecting new CRS

    Args:
        crs (list): Queryied CRS information from projpicker
    """

    # Create CRS info and area dicts
    options = {}
    area = {}
    projection_types = []
    units = []
    for entry in crs:
        # Generate hashed list dict for easier query

        crs_code = entry[2]

        crs_type = entry[0]
        if crs_type not in projection_types:
            projection_types.append(crs_type)

        authority = entry[1]
        crs_unit = entry[7]
        if crs_unit not in units:
            units.append(crs_unit)

        b, t, l, r, crs_area = entry[-5:]

        crs_dict = {
                "crs_type": crs_type,
                "authority": authority,
                "unit": crs_unit,
                "bbox": [b, t, l, r],
                "area": crs_area
                }

        arcpy.AddMessage(crs_dict)

        # Create main info dict queryable by code
        options[crs_code] = crs_dict
        # Create area dict for easy sorting
        area[crs_code] = crs_area

    # Sort by area to get most localized proj
    area_s = sorted(area.keys(), key=lambda k: area[k])
    # Sort options dict by area
    options_s = {}
    for entry in area_s:
        options_s[entry] = f"{options.get(entry).get('authority')}:{entry}"

    # Main window
    window = tk.Tk()
    window.geometry("1000x900")
    window.title("ProjPicker Geometry Creation (ArcGIS Pro)")

    # Text for CRS Info
    T = tk.Text(window, height = 5, width = 40)
    T.pack(side=tk.RIGHT, fill=tk.BOTH, anchor=tk.NE)
    T.insert(tk.END, "Use 'CRS Info' to show projection info")

    # Add scrollbar for list
    scrollbar = tk.Scrollbar(window)
    scrollbar.pack(side = tk.LEFT, fill = tk.BOTH)

    # List of crs
    crs_listbox = tk.Listbox(window)
    crs_listbox.pack(fill='x', ipady=150, anchor=tk.NW)
    for values in options_s.values():
        crs_listbox.insert(tk.END, values)

    # List box for projection type
    type_listbox = tk.Listbox(window)
    for t in projection_types:
        type_listbox.insert(tk.END, t)

    # List of units
    unit_listbox = tk.Listbox(window)
    for unit in units:
        unit_listbox.insert(tk.END, unit)
    unit_scrollbar = tk.Scrollbar(window)

    # Add widgets
    crs_listbox.config(yscrollcommand = scrollbar.set)
    scrollbar.config(command = crs_listbox.yview)

    unit_listbox.config(xscrollcommand=unit_scrollbar.set)
    unit_scrollbar.config(command=unit_listbox.xview)

    # Retrieve selected CRS from List
    def selected_item():
        global sel_crs
        for i in crs_listbox.curselection():

            # get auth:code string
            sel_code = crs_listbox.get(i)
            # get just code
            sel_auth = options.get(sel_code.split(":")[1])
            # update sel_crs
            sel_crs = sel_code
            # Close window
            window.destroy()

    # Show CRS info in right panel
    def get_info():
        for i in crs_listbox.curselection():
            # get auth:code string
            sel_code = crs_listbox.get(i)
            # get full ppik return json
            sel_auth = options.get(sel_code.split(":")[1])
            # format json
            pp = json.dumps(sel_auth, indent=2, sort_keys=True)
            # delete previous text
            T.delete('1.0', tk.END)
            # insert new text
            T.insert(tk.END, pp)

    def query_unit():
        for i in unit_listbox.curselection():
            sel_unit = unit_listbox.get(i)

            crs_listbox.delete(0,tk.END)

            for values in options_s.values():
                code = options.get(values.split(":")[1])
                if code.get("unit") == sel_unit:
                    crs_listbox.insert(tk.END, values)

    def query_crs_type():
        for i in type_listbox.curselection():
            sel_type = type_listbox.get(i)

            crs_listbox.delete(0, tk.END)
            for values in options_s.values():
                code = options.get(values.split(":")[1])
                if code.get("crs_type") == sel_type:
                    crs_listbox.insert(tk.END, values)


    def clear_filter():
        crs_listbox.delete(0, tk.END)
        for values in options_s.values():
            crs_listbox.insert(tk.END, values)


    # Buttons
    btn = tk.Button(window, text='OK', command=selected_item)
    btn.pack(side="bottom", fill='x', anchor=tk.SW)
    btn1 = tk.Button(window, text="CRS Info", command=get_info)
    btn1.pack(side="bottom", fill='x')
    btn2 = tk.Button(window, text="Filter unit", command=query_unit)
    btn2.pack(side="bottom", fill='x')
    btn3 = tk.Button(window, text="Filter type", command=query_crs_type)
    btn3.pack(side="bottom", fill='x')
    btn4 = tk.Button(window, text="Clear filter", command=clear_filter)
    btn4.pack(side="bottom", fill='x')
    type_listbox.pack(fill='both', side='left', expand=True)
    unit_listbox.pack(fill='both', side='left', expand=True)
    unit_scrollbar.pack(side='left', fill='y')

    # insert list into window
    crs_listbox.pack()

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
        crs = ppik.query_bboxes([[b, t, l, r]])

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

