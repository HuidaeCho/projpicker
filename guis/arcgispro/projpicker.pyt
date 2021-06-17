# vim: filetype=python tabstop=4 shiftwidth=4 expandtab smarttab autoindent
"""
This module implements the ArcGIS Pro toolbox of ProjPicker.

Tools: CreateFeatureClass,
       GuessFeatureClassProjection,
       GuessRasterProjection,
       ReprojectFeatureClass,
       ReprojectRaster,
       MatchCoordinates
"""

import arcpy
import os
import sys
from pathlib import Path
import textwrap
import projpicker as ppik



################################################################################
# Constants

WGS84 = 4326

PROJPICKER_UNITS = [
        "degree",
        "meter",
        "US foot",
        "degree minute second hemisphere",
        "grad",
        "kilometer",
        "50 kilometers",
        "150 kilometers",
        "link",
        "foot",
        "British foot (1936)",
        "British foot (Sears 1922)",
        "British yard (Sears 1922)",
        "British chain (Benoit 1895 B)",
        "British chain (Sears 1922 truncated)",
        "British chain (Sears 1922)",
        "Clarke's link",
        "Clarke's foot",
        "Clarke's yard",
        "German legal meter",
        "Gold Coast foot",
        "Indian yard (1937)",
        "Indian yard"
        ]

################################################################################
# Tkinter GUI

# Add path for add current path for tkinter to run
sys.argv = [str(Path(__file__))]


################################################################################
# Misc Functions

def check_unit(unit):
    if unit != "any" and not unit in PROJPICKER_UNITS:
        arcpy.AddError(f"Incorrect unit specified. Choose one of {PROJPICKER_UNITS}")


def run_gui(crs):
    # Run GUI and return the selected CRS
    sel_crs = ppik.gui.select_bbox(crs, True,
                                   lambda b: textwrap.dedent(f"""\
        CRS Type: {b.proj_table.replace("_crs", "").capitalize()}
        CRS Code: {b.crs_auth_name}:{b.crs_code}
        Unit:     {b.unit}
        South:    {b.south_lat}°
        North:    {b.north_lat}°
        West:     {b.west_lon}°
        East:     {b.east_lon}°
        Area:     {b.area_sqkm:n} sqkm"""))

    sel_crs = sel_crs[0] if len(sel_crs) > 0 else None
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
        self.tools = [CreateFeatureClass,
                      GuessFeatureClassProjection,
                      GuessRasterProjection,
                      ReprojectFeatureClass,
                      ReprojectRaster,
                      MatchCoordinates
                     ]


class CreateFeatureClass(object):
    def __init__(self):
        '''Define the tool (tool name is the name of the class).'''
        self.label = 'Create Feature Class'
        self.description = 'ProjPicker wrapper to create feature class'
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
                displayName='Output Feature',
                name='Feature',
                datatype='DEFeatureClass',
                parameterType='Required',
                direction='Output')

        unit = arcpy.Parameter(
                displayName='Unit',
                name='Unit',
                datatype='GPString',
                parameterType='Optional',
                direction='Input')
        unit.value = 'any'

        params = [feature, new_feat, unit]
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
        unit = parameters[2].valueAsText
        check_unit(unit)

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
        crs = ppik.query_bbox([b, t, l, r], unit=unit)

        sel_crs = run_gui(crs)


        # Get file path of output geometry
        desc = arcpy.Describe(new_feat)
        out_dir = desc.path
        out_file = desc.name

        # Create spatial reference object
        # MUST be integer so IGNF authority codes will not work
        try:
            spat_ref = arcpy.SpatialReference(int(sel_crs.crs_code))
        except RuntimeError:
            arcpy.AddError(f"Selected projection {sel_crs} is not avaible in ArcGIS Pro")
        # Create output geometry
        arcpy.management.CreateFeatureclass(out_dir, out_file,
                spatial_reference=spat_ref)

        return

class GuessFeatureClassProjection(object):
    def __init__(self):
        '''Define the tool (tool name is the name of the class).'''
        self.label = 'Guess Feature Class Projection'
        self.description = 'ProjPicker wrapper to guess missing projection'
        self.canRunInBackground = False

    def getParameterInfo(self):
        '''Define parameter definitions'''
        feature = arcpy.Parameter(
                displayName='Missing Projection Data',
                name='Missing Projection Data',
                datatype='DEFeatureClass',
                parameterType='required',
                direction='Input')

        location = arcpy.Parameter(
                displayName='Location of Data',
                name='Location',
                datatype='GPFeatureRecordSetLayer',
                parameterType='Required',
                direction='Input')

        unit = arcpy.Parameter(
                displayName='Unit',
                name='Unit',
                datatype='GPString',
                parameterType='Optional',
                direction='Input')
        unit.value = 'any'

        params = [feature, location, unit]
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
        location = parameters[1]
        unit = parameters[2].valueAsText
        check_unit(unit)

        # Get path of spatial query feature
        desc = arcpy.Describe(location)

        # get extent in lat lon of the data location
        bbox = desc.extent.projectAs(arcpy.SpatialReference(WGS84))

        b = bbox.YMin
        t = bbox.YMax
        l = bbox.XMin
        r = bbox.XMax

        # get extent in xy of the missing projection data
        desc = arcpy.Describe(feature)
        unproj_bbox = desc.extent

        ub = unproj_bbox.YMin
        ut = unproj_bbox.YMax
        ul = unproj_bbox.XMin
        ur = unproj_bbox.XMax


        # get full path of feature class
        feature_dir = desc.path
        feature_name = desc.name

        arcpy.AddMessage(f"Querying CRS's within {[b, t, l, r]}")

        # Query with guessed location and missing projection feature class
        crs = ppik.query_mixed_geoms([f'unit={unit}', 'bbox',
                                      'xy', [ub,ut, ul, ur],
                                      'latlon', [b, t, l, r]])

        sel_crs = run_gui(crs)


        # Create spatial reference object
        # MUST be integer so IGNF authority codes will not work
        try:
            spat_ref = arcpy.SpatialReference(int(sel_crs.crs_code))
        except RuntimeError:
            arcpy.AddError(f"Selected projection {sel_crs} is not avaible in ArcGIS Pro")
        # Create output geometry
        arcpy.DefineProjection_management(os.path.join(feature_dir, feature_name), spat_ref)

        return

class GuessRasterProjection(object):
    def __init__(self):
        '''Define the tool (tool name is the name of the class).'''
        self.label = 'Guess Raster Projection'
        self.description = 'ProjPicker wrapper to guess missing projection'
        self.canRunInBackground = False

    def getParameterInfo(self):
        '''Define parameter definitions'''
        raster = arcpy.Parameter(
                displayName='Missing Projection Raster',
                name='Missing Projection Raster',
                datatype='DERasterDataset',
                parameterType='required',
                direction='Input')

        location = arcpy.Parameter(
                displayName='Location of Data',
                name='Location',
                datatype='GPFeatureRecordSetLayer',
                parameterType='Required',
                direction='Input')

        unit = arcpy.Parameter(
                displayName='Unit',
                name='Unit',
                datatype='GPString',
                parameterType='Optional',
                direction='Input')
        unit.value = 'any'

        params = [raster, location, unit]
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
        raster = parameters[0]
        location = parameters[1]
        unit = parameters[2].valueAsText
        check_unit(unit)

        # Get path of spatial query raster
        desc = arcpy.Describe(location)

        # get extent in lat lon of the data location
        bbox = desc.extent.projectAs(arcpy.SpatialReference(WGS84))

        b = bbox.YMin
        t = bbox.YMax
        l = bbox.XMin
        r = bbox.XMax

        # get extent in xy of the missing projection data
        desc = arcpy.Describe(raster)
        unproj_bbox = desc.extent

        ub = unproj_bbox.YMin
        ut = unproj_bbox.YMax
        ul = unproj_bbox.XMin
        ur = unproj_bbox.XMax

        # get full path of raster class
        raster_dir = desc.path
        raster_name = desc.name

        arcpy.AddMessage(f"Querying CRS's within {[b, t, l, r]}")

        # Query with guessed location and missing projection raster class
        crs = ppik.query_mixed_geoms([f'unit={unit}', 'bbox',
                                      'xy', [ub,ut, ul, ur],
                                      'latlon', [b, t, l, r]])

        sel_crs = run_gui(crs)

        # Create spatial reference object
        # MUST be integer so IGNF authority codes will not work
        try:
            spat_ref = arcpy.SpatialReference(int(sel_crs.crs_code))
        except RuntimeError:
            arcpy.AddError(f"Selected projection {sel_crs} is not avaible in ArcGIS Pro")
        arcpy.DefineProjection_management(os.path.join(raster_dir, raster_name), spat_ref)

        return

class ReprojectFeatureClass(object):
    def __init__(self):
        '''Define the tool (tool name is the name of the class).'''
        self.label = 'Reproject Feature Class'
        self.description = 'ProjPicker wrapper to guess missing projection'
        self.canRunInBackground = False

    def getParameterInfo(self):
        '''Define parameter definitions'''
        feature = arcpy.Parameter(
                displayName='Input Feature Class',
                name='InFeature',
                datatype='DEFeatureClass',
                parameterType='required',
                direction='Input')

        new_feat = arcpy.Parameter(
                displayName='Output Feature',
                name='Feature',
                datatype='DEFeatureClass',
                parameterType='Required',
                direction='Output')

        location = arcpy.Parameter(
                displayName='Spatial Query',
                name='Location',
                datatype='GPFeatureRecordSetLayer',
                parameterType='Required',
                direction='Input')

        unit = arcpy.Parameter(
                displayName='Unit',
                name='Unit',
                datatype='GPString',
                parameterType='Optional',
                direction='Input')
        unit.value = 'any'

        params = [feature, new_feat, location, unit]
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
        location = parameters[2]
        unit = parameters[3].valueAsText
        check_unit(unit)

        # Get path of spatial query feature
        desc = arcpy.Describe(location)

        # get extent in lat lon
        bbox = desc.extent.projectAs(arcpy.SpatialReference(WGS84))

        b = bbox.YMin
        t = bbox.YMax
        l = bbox.XMin
        r = bbox.XMax

        arcpy.AddMessage(f"Querying CRS's within {[b, t, l, r]}")

        # If querying shape is a point then query by point
        # else use bounding box
        crs = ppik.query_bbox([b, t, l, r], unit=unit)

        sel_crs = run_gui(crs)

        # Get file path of input geom
        desc = arcpy.Describe(feature)
        in_file = f"{desc.path}\{desc.name}"

        # Get file path of output geo
        desc = arcpy.Describe(new_feat)
        out_file = f"{desc.path}\{desc.name}"

        # Create spatial reference object
        # MUST be integer so IGNF authority codes will not work
        try:
            spat_ref = arcpy.SpatialReference(int(sel_crs.crs_code))
        except RuntimeError:
            arcpy.AddError(f"Selected projection {sel_crs} is not avaible in ArcGIS Pro")
        # Create output geometry
        arcpy.management.Project(in_file, out_file, spat_ref)

class ReprojectRaster(object):
    def __init__(self):
        '''Define the tool (tool name is the name of the class).'''
        self.label = 'Reproject Raster'
        self.description = 'ProjPicker wrapper to guess missing projection'
        self.canRunInBackground = False

    def getParameterInfo(self):
        '''Define parameter definitions'''
        raster = arcpy.Parameter(
                displayName='Input Feature Class',
                name='InFeature',
                datatype='DERasterDataset',
                parameterType='required',
                direction='Input')

        new_feat = arcpy.Parameter(
                displayName='Output Feature',
                name='Feature',
                datatype='DERasterDataset',
                parameterType='Required',
                direction='Output')

        location = arcpy.Parameter(
                displayName='Spatial Query',
                name='Location',
                datatype='GPFeatureRecordSetLayer',
                parameterType='Required',
                direction='Input')

        unit = arcpy.Parameter(
                displayName='Unit',
                name='Unit',
                datatype='GPString',
                parameterType='Optional',
                direction='Input')
        unit.value = 'any'

        params = [raster, new_feat, location, unit]
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
        raster = parameters[0]
        new_feat = parameters[1]
        location = parameters[2]
        unit = parameters[3].valueAsText
        check_unit(unit)

        # Get path of spatial query raster
        desc = arcpy.Describe(location)

        # get extent in lat lon
        bbox = desc.extent.projectAs(arcpy.SpatialReference(WGS84))

        b = bbox.YMin
        t = bbox.YMax
        l = bbox.XMin
        r = bbox.XMax

        arcpy.AddMessage(f"Querying CRS's within {[b, t, l, r]}")

        # If querying shape is a point then query by point
        # else use bounding box
        crs = ppik.query_bbox([b, t, l, r], unit=unit)

        sel_crs = run_gui(crs)

        # Get file path of input geom
        desc = arcpy.Describe(raster)
        in_file = f"{desc.path}\{desc.name}"

        # Get file path of output geo
        desc = arcpy.Describe(new_feat)
        out_file = f"{desc.path}\{desc.name}"

        # Create spatial reference object
        # MUST be integer so IGNF authority codes will not work
        try:
            spat_ref = arcpy.SpatialReference(int(sel_crs.crs_code))
        except RuntimeError:
            arcpy.AddError(f"Selected projection {sel_crs} is not avaible in ArcGIS Pro")
        # Create output geometry
        arcpy.management.ProjectRaster(in_file, out_file, spat_ref)


class MatchCoordinates(object):
    def __init__(self):
        '''Define the tool (tool name is the name of the class).'''
        self.label = 'Match Coordinates'
        self.description = 'ProjPicker wrapper to guess missing projection'
        self.canRunInBackground = False

    def getParameterInfo(self):
        '''Define parameter definitions'''
        feature = arcpy.Parameter(
                displayName='Missing XY',
                name='XY',
                datatype='GPString',
                parameterType='Optional',
                direction='Input')

        location = arcpy.Parameter(
                displayName='Destination LatLon',
                name='latlon',
                datatype='GPString',
                parameterType='Optional',
                direction='Input')

        unit = arcpy.Parameter(
                displayName='Unit',
                name='Unit',
                datatype='GPString',
                parameterType='Optional',
                direction='Input')
        unit.value = 'any'

        match_max = arcpy.Parameter(
                displayName='Max Match',
                name='MaxMatch',
                datatype='GPString',
                parameterType='Optional',
                direction='Input')
        match_max.value = '1'

        tolerance = arcpy.Parameter(
                displayName='Match Tolerance',
                name='Tolerance',
                datatype='GPString',
                parameterType='Optional',
                direction='Input')
        params = [feature, location, unit, match_max, tolerance]
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

        # Add path to projpicker module
        sys.path.insert(0, str(Path(__file__).parent / 'projpicker'))

        # Read parameters
        feature = parameters[0].valueAsText
        location = parameters[1].valueAsText
        unit = parameters[2].valueAsText
        max = int(parameters[3].valueAsText)
        tolerance = int(parameters[4].valueAsText)

        check_unit(unit)

        # If querying shape is a point then query by point
        # else use bounding box
        xy = " ".join(feature).replace(" ", "")
        latlon = " ".join(location).replace(" ", "")

        query = f"postfix match_max={max} match_tol={tolerance} {latlon} xy {xy} match"
        crs = ppik.query_mixed_geoms(query)

        sel_crs = run_gui(crs)

        arcpy.AddMessage(sel_crs)

