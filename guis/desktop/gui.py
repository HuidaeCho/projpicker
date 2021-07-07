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
    def __init__(self, layout, *args, **kwargs):
        if layout not in ("big_list", "big_map"):
            raise ValueError(f"{layout}: Invalid layout; "
                             "Use big_list or big_map")

        wx.Frame.__init__(self, *args, **kwargs)
        self.panel = wx.Panel(self)

        main_size = wx.Size(900, 700)

        if layout == "big_list":
            # Sizers for layout
            main = wx.BoxSizer(wx.HORIZONTAL)
            left = wx.BoxSizer(wx.VERTICAL)
            bottom_left = wx.BoxSizer(wx.HORIZONTAL)
            bottom_right = wx.BoxSizer(wx.HORIZONTAL)
            right = wx.BoxSizer(wx.VERTICAL)

            # Widget sizes and parents
            left.SetMinSize(main_size.Width // 2, main_size.Height)
            right.SetMinSize(main_size.Width - left.MinSize.Width,
                             left.MinSize.Height)

            crs_listbox_parent = left
            crs_listbox_size = wx.Size(crs_listbox_parent.MinSize.Width,
                                       crs_listbox_parent.MinSize.Height)

            select_buttons_parent = bottom_left

            crs_info_parent = right
            crs_info_size = wx.Size(crs_info_parent.MinSize.Width, 125)
            map_parent = right
            map_size = wx.Size(map_parent.MinSize.Width,
                               main_size.Height - crs_info_size.Height)
            logical_buttons_parent = bottom_right
        elif layout == "big_map":
            # Sizers for layout
            main = wx.BoxSizer(wx.VERTICAL)
            top = wx.BoxSizer(wx.VERTICAL)
            top_bottom = wx.BoxSizer(wx.HORIZONTAL)
            bottom = wx.BoxSizer(wx.HORIZONTAL)
            bottom_left = wx.BoxSizer(wx.VERTICAL)
            bottom_left_bottom = wx.BoxSizer(wx.HORIZONTAL)
            bottom_right = wx.BoxSizer(wx.VERTICAL)

            # Widget sizes and parents
            top.SetMinSize(main_size.Width, main_size.Height // 2)
            bottom.SetMinSize(main_size.Width,
                              main_size.Height - top.MinSize.Height)
            bottom_left.SetMinSize(bottom.MinSize.Width // 2,
                                   bottom.MinSize.Height)
            bottom_right.SetMinSize(
                    bottom.MinSize.Width - bottom_left.MinSize.Width,
                    bottom.MinSize.Height)

            crs_listbox_parent = bottom_left
            crs_listbox_size = wx.Size(crs_listbox_parent.MinSize.Width,
                                       crs_listbox_parent.MinSize.Height)

            select_buttons_parent = bottom_left_bottom

            crs_info_parent = bottom_right
            crs_info_size = wx.Size(crs_info_parent.MinSize.Width,
                                    crs_info_parent.MinSize.Height)
            map_parent = top
            map_size = wx.Size(map_parent.MinSize.Width,
                               map_parent.MinSize.Height)
            logical_buttons_parent = top_bottom

        # Add widgets
        self.add_crs_listbox(crs_listbox_parent, crs_listbox_size)
        self.add_select_buttons(select_buttons_parent)

        self.add_crs_info(crs_info_parent, crs_info_size)
        self.add_map(map_parent, map_size)
        self.add_logical_buttons(logical_buttons_parent)

        # Add panels to main
        if layout == "big_list":
            left.Add(bottom_left, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 5)
            right.Add(bottom_right, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
            main.Add(left, 0, wx.ALIGN_LEFT | wx.LEFT, 5)
            main.Add(right, wx.ALIGN_RIGHT)
        elif layout == "big_map":
            top.Add(top_bottom, 0, wx.ALIGN_CENTER | wx.TOP, 5)
            bottom_left.Add(bottom_left_bottom, 0, wx.TOP, 5)
            bottom.Add(bottom_left, 0, wx.ALIGN_LEFT | wx.LEFT, 5)
            bottom.Add(bottom_right, wx.ALIGN_RIGHT)
            main.Add(top, 0, wx.ALIGN_TOP | wx.TOP, 5)
            main.Add(bottom, wx.ALIGN_BOTTOM)

        # Set sizer for main container
        self.panel.SetSizer(main)

        self.SetSize(main_size)
        self.SetMinSize(main_size)
        self.SetMaxSize(main_size)

        # All selection events are contained within following event.
        # This is done to allow the crslist selection and the drawing of the
        # selection CRS's bounding box to communicate witheach other.
        # Additionally, RunScript() is unable to run unless it is run within a
        # member function bound by wx.html2 event.
        wx.EvtHandler.Bind(self, wx.html2.EVT_WEBVIEW_LOADED, self.on_load_map)

        self.Show()

        self.crs = None
        self.selected_crs = None


    #################################
    # Left Frame
    def add_crs_listbox(self, parent, size):
        text = wx.StaticText(self.panel, 0, "Select a CRS", pos=(0, 0))
        parent.Add(text, 0, wx.CENTER | wx.TOP | wx.BOTTOM, 10)

        # CRS Choice listbox
        self.crs_listbox = wx.ListBox(self.panel, id=1, size=size,
                                      choices=["Draw geometry to query CRSs"])

        # Add CRS listbox to main left side
        parent.Add(self.crs_listbox, 1, wx.ALIGN_RIGHT | wx.ALL | wx.BOTTOM, 0)


    def add_select_buttons(self, parent):
        # Select button
        select_button = wx.Button(self.panel, label="Select")
        select_button.Bind(wx.EVT_BUTTON, self.on_select)

        # Cancel button
        cancel_button = wx.Button(self.panel, label="Cancel")
        cancel_button.Bind(wx.EVT_BUTTON, self.on_close)

        # Add buttons to parent
        parent.Add(select_button, 1)
        parent.AddStretchSpacer()
        parent.Add(cancel_button, 1)


    #################################
    # Right Frame
    def add_crs_info(self, parent, size):
        # CRS Info
        # Add header
        header = wx.StaticText(self.panel, 0, "CRS Info")

        # Set static box
        crs_info_box = wx.StaticBox(self.panel, 0, style=wx.ALIGN_CENTER)
        # Create sizer for the box
        crs_info_vsizer = wx.StaticBoxSizer(crs_info_box, wx.HORIZONTAL)
        crs_info_hsizer = wx.BoxSizer(wx.VERTICAL)
        # Input text
        self.crs_info_text = wx.StaticText(self.panel, -1, "",
                                           style=wx.ALIGN_LEFT, size=size)

        # Add text to correct sizer
        crs_info_vsizer.Add(self.crs_info_text, 1, wx.EXPAND, 100)
        crs_info_hsizer.Add(crs_info_vsizer, 1, wx.ALIGN_CENTER, 10)
        # Create border
        # https://www.blog.pythonlibrary.org/2019/05/09/an-intro-to-staticbox-and-staticboxsizers/
        border = wx.BoxSizer(wx.HORIZONTAL)
        border.Add(crs_info_hsizer, 0,
                   wx.BOTTOM | wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        # Add widgets to parent
        parent.Add(header, 0, wx.CENTER | wx.TOP, 10)
        parent.Add(border, 1, wx.ALIGN_RIGHT, 100)


    def add_map(self, parent, size):
        # Create webview
        self.browser = wx.html2.WebView.New(self.panel, size=size)

        # Load the local html
        url = wx.FileSystem.FileNameToURL(MAP_HTML)
        self.browser.LoadURL(url)
        parent.Add(self.browser, 1, wx.EXPAND | wx.RIGHT | wx.LEFT, 10)


    def add_logical_buttons(self, parent):
        # Higher level abstraction to bind buttons
        def create_button(op):
            button = wx.RadioButton(self.panel, label=op)
            button.Bind(wx.EVT_RADIOBUTTON, self.on_switch_logical_operator)
            return button

        self.logical_operator = "and"
        for op in ("and", "or", "xor"):
            if op != "and":
                parent.AddStretchSpacer()
            parent.Add(create_button(op), 1)


    #################################
    # Event Handlers
    def on_load_map(self, event):
        if DEBUG:
            # Confirm map is loaded for debugging purposes
            print("OpenStreetMap loaded.")

        # Handler for the Document title change to read the JSON and trigger
        # the ProjPicker query; This event will trigger the ProjPicker query
        # and population of the CRS list
        wx.EvtHandler.Bind(self, wx.html2.EVT_WEBVIEW_TITLE_CHANGED,
                           self.on_pull)

        # List box selection is within wx.html2.EVT_WEBVIEW_LOADED event
        # listener in order to allow any JS scripts which rely on selected
        # CRS info to be ran.
        wx.EvtHandler.Bind(self, wx.EVT_LISTBOX, self.on_select_crs)


    def on_switch_logical_operator(self, event):
        self.logical_operator = event.GetEventObject().Label
        self.query()
        if DEBUG:
            print("Chosen logical operator: ", self.logical_operator)


    def on_pull(self, event):
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
        if geom_chunk == "pull":
            self.geom_buf = ""
        elif geom_chunk == "done":
            self.json = json.loads(self.geom_buf)
            self.query()
            return
        elif hasattr(self, "geom_buf"):
            self.geom_buf += geom_chunk
        self.browser.RunScript("pushGeometryChunk()")


    def on_select_crs(self, event):
        # Populate CRS info with information of selected CRS
        crs_info = ""
        crs = self.find_selected_crs()
        if crs is not None:
            crs_info = self.get_crs_info(crs)
        self.crs_info_text.SetLabel(crs_info)

        crs_bbox_feature = self.create_crs_bbox_feature(crs)
        self.browser.RunScript(f"drawCRSBBox({crs_bbox_feature})")


    def on_select(self, event):
        self.selected_crs = self.find_selected_crs()
        self.Destroy()


    def on_close(self, event):
        self.Destroy()


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
            geoms.extend([geom.type, geom.coors])

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


if __name__ == "__main__":
    app = wx.App()
    ppik_gui = ProjPickerGUI("big_list", None)
    app.MainLoop()
    ppik_gui.print_selected_crs_auth_code()
