# vim: filetype=python tabstop=4 shiftwidth=4 expandtab smarttab autoindent
import arcpy
import os
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk
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
    window.geometry("1000x500")
    window.title("ProjPicker Geometry Creation (ArcGIS Pro)")

    style = ttk.Style(window)
    style.theme_use('winnative')

    # Text for CRS Info
    T = tk.Text(window, height = 5, width = 30)
    T.insert(tk.END, "Use 'CRS Info' to show projection info")

    # Add scrollbar for list
    scrollbar = tk.Scrollbar(window)
    scrollbar.pack(side = tk.LEFT, fill = tk.BOTH)

    # List of crs
    crs_listbox = tk.Listbox(window)
    for values in options_s.values():
        crs_listbox.insert(tk.END, values)

    # List box for projection type
    type_combobox = ttk.Combobox(window)
    projection_types.insert(0, 'All')
    type_combobox['values'] = projection_types
    type_combobox.set('CRS Type')

    # List of units
    unit_combobox = ttk.Combobox(window)
    units.insert(0, 'All')
    unit_combobox['values'] = units
    unit_combobox.set('Unit')


    # Add widgets
    crs_listbox.config(yscrollcommand = scrollbar.set)
    scrollbar.config(command = crs_listbox.yview)

    def make_display_text(sel, code):
        new_text = (f"CRS Type: {sel.get('crs_type')}\n"
                    f"CRS Code: {code}\n"
                    f"Unit:     {sel.get('unit')}\n"
                    f"South:    {sel.get('bbox')[0]}°\n"
                    f"North:    {sel.get('bbox')[1]}°\n"
                    f"West:     {sel.get('bbox')[2]}°\n"
                    f"East:     {sel.get('bbox')[3]}°\n"
                    f"Area:     {sel.get('area'):n} sqkm\n"
                    )
        return new_text

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
            text = make_display_text(sel_auth, sel_code)
            # delete previous text
            T.delete('1.0', tk.END)
            # insert new text
            T.insert(tk.END, text)

    def query_unit():
        sel_unit = units[unit_combobox.current()]
        if sel_unit == 'All':
            clear_filter()

        else:
            crs_listbox.delete(0,tk.END)
            for values in options_s.values():
                code = options.get(values.split(":")[1])
                if code.get("unit") == sel_unit:
                    crs_listbox.insert(tk.END, values)

    def query_crs_type():
        sel_type = projection_types[type_combobox.current()]
        if sel_type == 'All':
            clear_filter()
        else:
            crs_listbox.delete(0, tk.END)
            for values in options_s.values():
                code = options.get(values.split(":")[1])
                if code.get("crs_type") == sel_type:
                    crs_listbox.insert(tk.END, values)


    def clear_filter():
        crs_listbox.delete(0, tk.END)
        for values in options_s.values():
            crs_listbox.insert(tk.END, values)
        unit_combobox.set('Unit')
        type_combobox.set('CRS Type')

    # Selection wrapper for updating CRS info
    def onselect_info(event):
        get_info()

    def onselect_unit(event):
        query_unit()

    def onselect_type(event):
        query_crs_type()

    def cancel():
        window.destroy()
        sys.exit(1)

    # Bind selection event to run onselect
    crs_listbox.bind("<<ListboxSelect>>", onselect_info)
    unit_combobox.bind("<<ComboboxSelected>>", onselect_unit)
    type_combobox.bind("<<ComboboxSelected>>", onselect_type)

    # Buttons
    btn = tk.Button(window, text='Create Feature Class', command=selected_item)
    btn.pack(side="right", fill='x', expand=True, anchor=tk.SE)
    btn1 = tk.Button(window, text="Cancel", command=cancel)
    btn1.pack(side="right", fill='x', expand=True, anchor=tk.SW)
    T.pack(fill='y', side='right', expand=True)
    crs_listbox.pack(fill='x', ipady=50, anchor=tk.NW)
    type_combobox.pack(fill='both', side='left', expand=True)
    unit_combobox.pack(fill='both', side='left', expand=True)

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

        params = [feature, new_feat]
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
        crs = ppik.query_bbox([b, t, l, r])

        # Run GUI and return the selected CRS
        sel_crs = popup(crs)

        # Get file path of output geometry
        desc = arcpy.Describe(new_feat)
        out_dir = desc.path
        out_file = desc.name

        # Create spatial reference object
        # MUST be integer so IGNF authority codes will not work
        try:
            spat_ref = arcpy.SpatialReference(int(sel_crs.split(':')[1]))
            # Create output geometry
            arcpy.management.CreateFeatureclass(out_dir, out_file,
                    spatial_reference=spat_ref)
        except RuntimeError:
            arcpy.AddError(f"Selected projection {sel_crs} is not avaible in ArcGIS Pro")

        return

