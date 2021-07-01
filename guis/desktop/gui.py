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
import textwrap
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
            reversed_coors = []
            for lonlat in coors[0]:
                reversed_coors.append(lonlat[::-1])
            self.coors = list(reversed_coors)


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
        self.create_buttons()

        # Add bottom left sizer to left side sizer
        self.main.Add(self.left, 0, wx.ALIGN_LEFT | wx.LEFT, 5)

        self.create_crs_info()
        self.create_map()

        self.crs = None

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
        # EVENTS

        # Confirm loading of map
        wx.EvtHandler.Bind(self, wx.html2.EVT_WEBVIEW_LOADED, self.confirm_load)

        # Handler for the Document title change to read the JSON and trigger
        # the ProjPicker query; This event will trigger the ProjPicker query
        # and population of the CRS list
        wx.EvtHandler.Bind(self, wx.html2.EVT_WEBVIEW_TITLE_CHANGED,
                           self.get_json)

        wx.EvtHandler.Bind(self, wx.EVT_LISTBOX, self.pop_info)


    #################################
    # LEFT
    def create_crs_listbox(self):
        st = wx.StaticText(self.panel, 0, "CRS List", pos=(0, 0))
        self.left.Add(st, 0, wx.CENTER | wx.TOP | wx.BOTTOM, 10)

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


    def create_buttons(self):
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
        self.left.Add(btm_left, 0, wx.BOTTOM)


    #################################
    # RIGHT
    def create_crs_info(self):
        # CRS INFO
        # Set static box
        crs_info_box = wx.StaticBox(self.panel, 0, "CRS Info")
        # Create sizer for the box
        crs_info_vsizer = wx.StaticBoxSizer(crs_info_box, wx.HORIZONTAL)
        crs_info_hsizer = wx.BoxSizer(wx.VERTICAL)
        # Input text
        self.crs_info_text = wx.StaticText(self.panel, -1, "",
                                           style=wx.ALIGN_LEFT, size=(600, 300))
        # Set font
        font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
        font.SetPointSize(15)
        self.crs_info_text.SetFont(font)

        # Add text to correct sizer
        crs_info_vsizer.Add(self.crs_info_text, 1, wx.EXPAND, 100)
        crs_info_hsizer.Add(crs_info_vsizer, 1, wx.EXPAND, 10)
        # Create border
        # https://www.blog.pythonlibrary.org/2019/05/09/an-intro-to-staticbox-and-staticboxsizers/
        border = wx.BoxSizer(wx.HORIZONTAL)
        border.Add(crs_info_hsizer, 0, wx.ALL | wx.EXPAND, 10)
        # Add to right column
        self.right.Add(border, 1, wx.ALIGN_RIGHT, 100)


    def create_map(self):
        # Create webview
        self.browser = wx.html2.WebView.New(self.panel)

        # Load the local html
        url = wx.FileSystem.FileNameToURL(MAP_HTML)
        self.browser.LoadURL(url)
        # Set sizer
        browser_size = wx.BoxSizer(wx.HORIZONTAL)
        self.right.Add(self.browser, 1, wx.EXPAND | wx.ALL, 10)


    def get_crs_info(self, crs: list):
        # Format CRS Info
        # Same as lambda function in projpicker.gui
        return textwrap.dedent(f"""\
        CRS Type: {crs.proj_table.replace("_crs", "").capitalize()}
        CRS Code: {crs.crs_auth_name}:{crs.crs_code}
        Unit:     {crs.unit}
        South:    {crs.south_lat}°
        North:    {crs.north_lat}°
        West:     {crs.west_lon}°
        East:     {crs.east_lon}°
        Area:     {crs.area_sqkm:n} sqkm""")


    def query(self):
        # Load all features drawn
        features = self.json["features"]

        # Create Geometry struct for each feature
        geoms = []
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
        crs_names = [crs.crs_name for crs in self.crs]
        self.crs_listbox.InsertItems(crs_names, 0)


    def construct_query_string(self, geom: Geometry):
        # Construct ProjPicker query
        return geom.type, geom.coors


    def find_selected_crs(self):
        sel_crs = None
        if self.crs is not None:
            sel_index = self.crs_listbox.GetSelection()
            if sel_index >= 0:
                sel_crs_name = self.crs_listbox.GetString(sel_index)
                for crs in self.crs:
                    if crs.crs_name == sel_crs_name:
                        sel_crs = crs
                        break
        return sel_crs


    #################################
    # Event Handlers
    def select(self, event):
        crs_auth_code = ""
        crs = self.find_selected_crs()
        if crs is not None:
            crs_auth_code = f"{crs.crs_auth_name}:{crs.crs_code}\n"
        print(crs_auth_code, end="")
        self.Close()


    def close(self, event):
        self.Close()


    def confirm_load(self, event):
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
        # 1000 chars; Implement a workaround using pull messages;
        # pushGeometryChunk() changes the title of HTML document within webview
        # to a chunk of JSON; Super hacky solution because other methods don't
        # work as expected

        geom_chunk = self.browser.GetCurrentTitle()
        if geom_chunk == "pull":
            self.geom_buf = ""
        elif geom_chunk == "done":
            self.json = json.loads(self.geom_buf)
            # Run query
            self.query()
            return
        else:
            self.geom_buf += geom_chunk
        self.browser.RunScript("pushGeometryChunk()")


    def pop_info(self, event):
        # Populate CRS info with information of selected CRS
        crs_info = ""
        crs = self.find_selected_crs()
        if crs is not None:
            crs_info = self.get_crs_info(crs)
        self.crs_info_text.SetLabel(crs_info)


if __name__ == "__main__":
    app = wx.App()
    ProjPickerGUI(None).Show()
    app.MainLoop()
