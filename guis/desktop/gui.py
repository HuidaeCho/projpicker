#!/usr/bin/env python3
################################################################################
# Project:  ProjPicker (Projection Picker) Desktop GUI
#           <https://github.com/HuidaeCho/projpicker>
# Authors:  Owen Smith, Huidae Cho
#           Institute for Environmental and Spatial Analysis
#           University of North Georgia
# Since:    June 30, 2021
#
# Copyright (C) 2021 Huidae Cho <https://faculty.ung.edu/hcho/> and
#                    Owen Smith <https://www.gaderian.io/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
################################################################################

import wx
import wx.html2
import json
import projpicker as ppik


#################################
# Constants
DEBUG = True
MAP_HTML = "map.html"


#################################
# Geometry
class Geometry:
    def __init__(self, type, coors):
        self.type = "poly" if type == "Polygon" else "point"

        # Reverse coordinates as leaflet returns opposite order of what
        # ProjPicker takes
        if self.type == "point":
            # Coordinates in "Point" type are single-depth tuple [i, j]
            self.coors = coors[::-1]
        else:
            # Coordinates in "Poly" type are in multi-depth array of size
            # [[[i0, j0], [i1, j1], ...]]; Move down array depth for easier
            # iteration
            latlon_coors = []
            for lonlat in coors[0]:
                latlon_coors.append(lonlat[::-1])
            self.coors = list(latlon_coors)


#################################
# GUI
class ProjPickerGUI(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.panel = wx.Panel(self)

        # Add left size for layout
        self.main = wx.BoxSizer(wx.HORIZONTAL)
        self.left = wx.BoxSizer(wx.VERTICAL)
        self.right = wx.BoxSizer(wx.VERTICAL)

        self.create_crs_listbox()
        self.create_select_buttons()

        # Add bottom left sizer to left side sizer
        self.main.Add(self.left, 0, wx.ALIGN_LEFT | wx.LEFT, 5)

        self.create_crs_info()
        self.create_map()
        self.create_logical_buttons()

        self.crs = None
        self.selected_crs = None

        # Add right to main
        self.main.Add(self.right, wx.ALIGN_RIGHT)
        # Set sizer for main container
        self.panel.SetSizer(self.main)

        width = 900
        height = 700
        size = wx.Size(width, height)
        self.SetMaxSize(size)
        self.SetMinSize(size)
        self.SetSize(size)

        #################################
        # Bind Event Handlers

        # Handler for the Document title change to read the JSON and trigger
        # the ProjPicker query; This event will trigger the ProjPicker query
        # and population of the CRS list
        wx.EvtHandler.Bind(self, wx.html2.EVT_WEBVIEW_TITLE_CHANGED,
                           self.get_json)

        # All selection events are contained within following event.
        # This is done to allow the crslist selection and the drawing of the
        # selection CRS's bounding box to communicate witheach other.
        # Additionally, RunScript() is unable to run unless it is run within a
        # member function bound by wx.html2 event.
        wx.EvtHandler.Bind(self, wx.html2.EVT_WEBVIEW_LOADED,
                self.selection_events)

        self.Show()


    #################################
    # Left Frame
    def create_crs_listbox(self):
        text = wx.StaticText(self.panel, 0, "Select a CRS", pos=(0, 0))
        self.left.Add(text, 0, wx.CENTER | wx.TOP | wx.BOTTOM, 10)

        self.left_width = 500
        self.left_height = 700

        # CRS Choice listbox
        self.crs_listbox = wx.ListBox(
            self.panel,
            id=1,
            size=(self.left_width, self.left_height),
            choices=["Draw geometry to query CRSs"],
        )

        # Add CRS listbox to main left side
        self.left.Add(self.crs_listbox, 1, wx.ALIGN_RIGHT | wx.ALL | wx.BOTTOM,
                      0)


    def create_select_buttons(self):
        # Space out buttons
        width = self.left_width // 7
        # Create bottom left sizer for buttons
        btm_left = wx.BoxSizer(wx.HORIZONTAL)
        # Select button
        select_button = wx.Button(self.panel, label="Select")
        select_button.Bind(wx.EVT_BUTTON, self.select)
        # Cancel button
        cancel_button = wx.Button(self.panel, label="Cancel")
        cancel_button.Bind(wx.EVT_BUTTON, self.close)
        # Add buttons to bottom left
        btm_left.Add(select_button, 1, wx.LEFT | wx.RIGHT, width)
        btm_left.Add(cancel_button, 1, wx.LEFT | wx.RIGHT, width)
        self.left.Add(btm_left, 0, wx.BOTTOM | wx.TOP, 4)


    #################################
    # Right Frame
    def create_crs_info(self):
        # CRS Info
        # Set static box
        crs_info_box = wx.StaticBox(self.panel, 0, style=wx.ALIGN_CENTER)
        # Create sizer for the box
        crs_info_vsizer = wx.StaticBoxSizer(crs_info_box, wx.HORIZONTAL)
        crs_info_hsizer = wx.BoxSizer(wx.VERTICAL)
        # Input text
        self.crs_info_text = wx.StaticText(self.panel, -1, "",
                                           style=wx.ALIGN_LEFT, size=(400, 300))

        # Add text to correct sizer
        crs_info_vsizer.Add(self.crs_info_text, 1, wx.EXPAND, 100)
        crs_info_hsizer.Add(crs_info_vsizer, 1, wx.ALIGN_CENTER, 10)
        # Create border
        # https://www.blog.pythonlibrary.org/2019/05/09/an-intro-to-staticbox-and-staticboxsizers/
        border = wx.BoxSizer(wx.HORIZONTAL)
        border.Add(crs_info_hsizer, 0,
                   wx.BOTTOM | wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        # Add text header
        text = wx.StaticText(self.panel, 0, "CRS Info")
        self.right.Add(text, 0, wx.CENTER | wx.TOP, 10)
        # Add to right column
        self.right.Add(border, 1, wx.ALIGN_RIGHT, 100)


    def create_map(self):
        # Create webview
        self.browser = wx.html2.WebView.New(self.panel)

        # Load the local html
        url = wx.FileSystem.FileNameToURL(MAP_HTML)
        self.browser.LoadURL(url)
        self.right.Add(self.browser, 1, wx.EXPAND | wx.RIGHT | wx.LEFT, 10)


    def create_logical_buttons(self):
        # Default
        self.logical_operator = "and"

        width = 400 // 11

        # Horizontal sizer for spacing
        btm_right = wx.BoxSizer(wx.HORIZONTAL)

        # AND
        and_button = wx.RadioButton(self.panel, label="and")
        btm_right.Add(and_button, 0, wx.LEFT | wx.RIGHT, width)
        # OR
        or_button = wx.RadioButton(self.panel, label="or")
        btm_right.Add(or_button, 0 ,wx.LEFT | wx.RIGHT, width)
        # XOR
        xor_button = wx.RadioButton(self.panel, label="xor")
        btm_right.Add(xor_button, 0, wx.LEFT | wx.RIGHT, width)

        # Add to main sizer
        self.right.Add(btm_right, 0, wx.TOP | wx.BOTTOM, 10)

        # Higher level abstraction to bind buttons
        def bind_button(button):
            button.Bind(wx.EVT_RADIOBUTTON, self.switch_logical_operator)

        bind_button(and_button)
        bind_button(or_button)
        bind_button(xor_button)


    #################################
    # Event Handlers
    def switch_logical_operator(self, event):
        self.logical_operator = event.GetEventObject().Label
        self.query()
        if DEBUG:
            print("Chosen logical operator: ", self.logical_operator)


    def select(self, event):
        self.selected_crs = self.find_selected_crs()
        self.Destroy()


    def close(self, event):
        self.Destroy()


    def confirm_load(self):
        if DEBUG:
            # Confirm map is loaded for debugging purposes
            print("OpenStreetMap loaded.")


    def get_json(self, event):
        # Get new JSON from title; Main event handler which will trigger
        # functionality

        # http://trac.wxwidgets.org/ticket/13859
        # https://wxpython.org/Phoenix/docs/html/wx.webkit.WebKitCtrl.html
        # XXX: RunScript() still returns None? GetSelected(Source|Text)() don't
        # work? GetPageSource() returns the original page source only;
        # GetPageText() returns an empty text; Document title can only grow to
        # 1000 characters; Implement a workaround using pull messages;
        # pushGeometryChunk() changes the title of HTML document within webview
        # to a chunk of JSON; Super hacky solution because other methods don't
        # work as documented

        geom_chunk = self.browser.GetCurrentTitle()
        if geom_chunk == "ProjPicker Desktop GUI Map":
            print("No geometry drawn at startup")
            return
        if geom_chunk == "pull":
            self.geom_buf = ""
        elif geom_chunk == "done":
            self.json = json.loads(self.geom_buf)
            # Run query
            self.query()
            return
        elif hasattr(self, "geom_buf"):
            self.geom_buf += geom_chunk
        self.browser.RunScript("pushGeometryChunk()")


    def pop_info(self, event):
        # Populate CRS info with information of selected CRS
        crs_info = ""
        crs = self.find_selected_crs()
        if crs is not None:
            crs_info = self.get_crs_info(crs)
        self.crs_info_text.SetLabel(crs_info)
        self.draw_crs_bbox(crs)


    def selection_events(self, event):
        # List box selection is within wx.html2.EVT_WEBVIEW_LOADED event
        # listener in order to allow any JS scripts which rely on selected
        # CRS info to be ran.
        wx.EvtHandler.Bind(self, wx.EVT_LISTBOX, self.pop_info)
        # Confirm loading of map
        self.confirm_load()


    def draw_crs_bbox(self, crs):
        # crs is a ProjPicker BBox instance; Run within pop_info event handler
        # to draw CRS bbox
        crs_bbox_feature = self.create_crs_bbox_feature(crs)
        self.browser.RunScript(f"drawCRSBBox({crs_bbox_feature})")


    #################################
    # Utilities
    def query(self):
        # Handle error when switching logical operators and no geometry is
        # drawn
        if not hasattr(self, "json"):
            return

        # Load all features drawn
        features = self.json["features"]

        # Create Geometry struct for each feature
        geoms = [self.logical_operator]
        for feature in features:
            json_geom = feature["geometry"]
            geom_type = json_geom["type"]
            coors = json_geom["coordinates"]
            geom = Geometry(json_geom["type"], json_geom["coordinates"])
            geoms.extend(self.construct_query_string(geom))

        # Query with ProjPicker
        self.crs = ppik.query_mixed_geoms(geoms)

        if DEBUG:
            print("Query geometries:", geoms)
            print("Number of queried CRSs:", len(self.crs))

        # Populate CRS listbox
        self.crs_listbox.Clear()
        crs_names = [f"{crs.crs_name} ({crs.crs_auth_name}:{crs.crs_code})"
                     for crs in self.crs]
        self.crs_listbox.InsertItems(crs_names, 0)


    def construct_query_string(self, geom: Geometry):
        # Construct ProjPicker query
        return geom.type, geom.coors


    def find_selected_crs(self):
        sel_crs = None
        sel_index = self.crs_listbox.GetSelection()
        if self.crs is not None and sel_index >= 0:
            sel_crs = self.crs[sel_index]
        return sel_crs


    def get_crs_info(self, crs):
        # Format CRS Info; Same as lambda function in projpicker.gui
        crs_info = f"""\
            CRS Type: {crs.proj_table.replace("_crs", "").capitalize()}
            CRS Code: {crs.crs_auth_name}:{crs.crs_code}
            Unit:     {crs.unit}
            South:    {crs.south_lat}°
            North:    {crs.north_lat}°
            West:     {crs.west_lon}°
            East:     {crs.east_lon}°
            Area:     {crs.area_sqkm:n} sqkm"""

        # align fields using tabs
        lines = crs_info.split("\n")
        pairs = []
        # calculate the max key length
        key_len = 0
        for line in lines:
            key, val = line.split(": ")
            key = key.strip()
            val = val.strip()
            key_len = max(len(key), key_len)
            pairs.append([key, val])
        # length of tabs
        key_len = (key_len // 8 + 1) * 8
        crs_info = ""
        for pair in pairs:
            key, val = pair
            # ceil: https://stackoverflow.com/a/17511341/16079666
            num_tabs = -(-(key_len - len(key)) // 8)
            crs_info += f"{key}:" + "\t" * num_tabs + f"{val}\n"
        return crs_info


    def get_crs_auth_code(self, crs):
        crs_auth_code = ""
        if crs is not None:
            crs_auth_code = f"{crs.crs_auth_name}:{crs.crs_code}"
        return crs_auth_code


    def print_crs_auth_code(self, crs):
        crs_auth_code = self.get_crs_auth_code(crs)
        print(crs_auth_code, end="" if crs_auth_code == "" else "\n")


    def print_selected_crs_auth_code(self):
        self.print_crs_auth_code(self.selected_crs)


    def get_selected_crs(self):
        return self.selected_crs

    def create_crs_bbox_feature(self, crs):
        # crs is a ProjPicker BBox instance

        # BBox => GeoJSON polygon
        s = crs.south_lat
        n = crs.north_lat
        w = crs.west_lon
        e = crs.east_lon
        coors = [[[w, n], [e, n], [e, s], [w,s]]]

        # Make GeoJSON to pass to JS
        crs_bbox_feature = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": coors
            }
        }

        return crs_bbox_feature


if __name__ == "__main__":
    app = wx.App()
    ppik_gui = ProjPickerGUI(None)
    app.MainLoop()
    ppik_gui.print_selected_crs_auth_code()
