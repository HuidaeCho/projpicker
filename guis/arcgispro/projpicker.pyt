"""
This module implements the ArcGIS Pro toolbox of ProjPicker.
"""

# vim: filetype=python tabstop=4 shiftwidth=4 expandtab smarttab autoindent
import arcpy
import os
import sys
from pathlib import Path
import projpicker as ppik

################################################################################
# Constants

WGS84 = 4326

################################################################################
# Tkinter GUI

# Add path for add current path for tkinter to run
sys.argv = [str(Path(__file__))]

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
        sel_crs = ppik.gui.select_bbox(crs)
        if len(sel_crs) > 0:
            sel_crs = sel_crs[0]
        else:
            sel_crs = None

        # Get file path of output geometry
        desc = arcpy.Describe(new_feat)
        out_dir = desc.path
        out_file = desc.name

        # Create spatial reference object
        # MUST be integer so IGNF authority codes will not work
        try:
            spat_ref = arcpy.SpatialReference(int(sel_crs.crs_code))
            # Create output geometry
            arcpy.management.CreateFeatureclass(out_dir, out_file,
                    spatial_reference=spat_ref)
        except RuntimeError:
            arcpy.AddError(f"Selected projection {sel_crs} is not avaible in ArcGIS Pro")

        return

