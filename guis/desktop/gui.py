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

import sys
import argparse
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
    def __init__(self, layout, geoms, *args, **kwargs):
        if layout not in ("big_list", "big_map"):
            raise ValueError(f"{layout}: Invalid layout; "
                             "Use big_list or big_map")

        self.geoms = geoms
        self.geom_buf = None
        self.json = None
        self.crs = None
        self.selected_crs = None
        self.map_loaded_count = 0

        # Create GUI
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

            crs_list_parent = left
            crs_list_size = wx.Size(crs_list_parent.MinSize.Width,
                                    crs_list_parent.MinSize.Height)

            select_buttons_parent = bottom_left

            line_height = self.panel.GetFont().GetPixelSize().Height * 1.025
            num_lines_crs_info = self.get_crs_info(None)

            crs_info_parent = right
            crs_info_size = wx.Size(crs_info_parent.MinSize.Width,
                                    int(num_lines_crs_info * line_height))

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

            crs_list_parent = bottom_left
            crs_list_size = wx.Size(crs_list_parent.MinSize.Width,
                                    crs_list_parent.MinSize.Height)

            select_buttons_parent = bottom_left_bottom

            crs_info_parent = bottom_right
            crs_info_size = wx.Size(crs_info_parent.MinSize.Width,
                                    crs_info_parent.MinSize.Height)

            map_parent = top
            map_size = wx.Size(map_parent.MinSize.Width,
                               map_parent.MinSize.Height)

            logical_buttons_parent = top_bottom

        # Add widgets
        self.add_crs_list(crs_list_parent, crs_list_size)
        self.add_select_buttons(select_buttons_parent)

        self.add_crs_info(crs_info_parent, crs_info_size)

        self.add_map(map_parent, map_size)
        self.add_logical_buttons(logical_buttons_parent)

        # Add panels to main
        if layout == "big_list":
            left.Add(bottom_left, 0, wx.ALIGN_CENTER | wx.BOTTOM, 5)
            right.Add(bottom_right, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 5)
            main.Add(left)
            main.Add(right)
        elif layout == "big_map":
            top.Add(top_bottom, 0, wx.ALIGN_CENTER)
            bottom_left.Add(bottom_left_bottom, 0, wx.ALIGN_CENTER | wx.BOTTOM,
                            5)
            bottom.Add(bottom_left)
            bottom.Add(bottom_right)
            main.Add(top)
            main.Add(bottom)

        # Set sizer for main container
        self.panel.SetSizer(main)

        self.SetSize(main_size)
        self.SetMinSize(main_size)
        self.SetMaxSize(main_size)

        self.Show()


    #################################
    # Map
    def add_map(self, parent, size):
        self.map = wx.html2.WebView.New(self.panel, size=size)
        self.map.LoadURL(wx.FileSystem.FileNameToURL(MAP_HTML))
        self.map.Bind(wx.html2.EVT_WEBVIEW_LOADED, self.on_load_map)
        self.map.Bind(wx.html2.EVT_WEBVIEW_TITLE_CHANGED, self.on_pull_geoms)

        parent.Add(self.map, 1, wx.ALL, 5)


    def add_logical_buttons(self, parent):
        # Higher level abstraction to bind buttons
        def create_button(op):
            button = wx.RadioButton(self.panel, label=op)
            button.Bind(wx.EVT_RADIOBUTTON, self.on_switch_logical_operator)
            return button

        self.logical_buttons = {}
        for op in ("and", "or", "xor"):
            if op != "and":
                parent.AddStretchSpacer()
            button = create_button(op)
            parent.Add(button, 1)
            self.logical_buttons[op] = button
        self.switch_logical_operator("and")


    #################################
    # CRS List
    def add_crs_list(self, parent, size):
        header = wx.StaticText(self.panel, 0, "Select a CRS", pos=(0, 0))

        self.crs_list = wx.ListCtrl(self.panel, size=size,
                                    style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.crs_list.AppendColumn("Name", width=parent.MinSize.Width - 100)
        self.crs_list.AppendColumn("Code", width=100)
        self.crs_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select_crs)

        parent.Add(header, 0, wx.CENTER | wx.TOP, 5)
        parent.Add(self.crs_list, 1, wx.ALL, 5)


    def add_select_buttons(self, parent):
        select_button = wx.Button(self.panel, label="Select")
        select_button.Bind(wx.EVT_BUTTON, self.on_select)

        cancel_button = wx.Button(self.panel, label="Cancel")
        cancel_button.Bind(wx.EVT_BUTTON, self.on_close)

        parent.Add(select_button, 1)
        parent.AddStretchSpacer()
        parent.Add(cancel_button, 1)


    #################################
    # CRS Info
    def add_crs_info(self, parent, size):
        header = wx.StaticText(self.panel, 0, "CRS Info")
        self.crs_info = wx.TextCtrl(self.panel, size=size,
                                    style=wx.TE_MULTILINE | wx.TE_READONLY)

        parent.Add(header, 0, wx.CENTER | wx.TOP, 5)
        parent.Add(self.crs_info, 1, wx.ALL, 5)


    #################################
    # Event Handlers
    def on_load_map(self, event):
        self.map_loaded_count += 1
        if self.map_loaded_count != 2:
            # XXX: EVT_WEBVIEW_LOADED is triggered twice? Drawing didn't work
            # on the first event
            return

        if self.geoms is None:
            return

        parsed_geoms = ppik.parse_mixed_geoms(self.geoms)

        features = []
        geom_type = "point"
        for geom in parsed_geoms:
            if geom in ("and", "or", "xor"):
                print(geom)
                self.switch_logical_operator(geom)
                continue
            elif geom in ("point", "poly", "bbox"):
                geom_type = geom
                continue
            elif type(geom) != list:
                # Ignore unsupported geometries
                continue
            if geom_type == "point":
                feature = self.create_geojson_feature("Point", geom[::-1])
            elif geom_type == "poly":
                feature = self.create_geojson_feature("Polygon", geom)
            else:
                s, n, w, e = geom
                coors = [[[w, n], [e, n], [e, s], [w, s]]]
                feature = self.create_geojson_feature("Polygon", coors)
            features.append(feature)

        self.map.RunScript(f"drawGeometries({features})")


    def on_switch_logical_operator(self, event):
        self.switch_logical_operator(event.GetEventObject().Label)


    def on_pull_geoms(self, event):
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

        geom_chunk = self.map.GetCurrentTitle()
        if geom_chunk == "pull":
            self.geom_buf = ""
        elif geom_chunk == "done":
            self.json = json.loads(self.geom_buf)
            self.query(self.create_parsable_geoms())
            return
        elif self.geom_buf is None:
            return
        else:
            self.geom_buf += geom_chunk
        self.map.RunScript("pushGeometryChunk()")


    def on_select_crs(self, event):
        # Populate CRS info with information of selected CRS
        crs_info = ""
        crs = self.find_selected_crs()
        if crs is not None:
            crs_info = self.get_crs_info(crs)
        self.crs_info.SetValue(crs_info)

        crs_bbox_feature = self.create_crs_bbox_feature(crs)
        self.map.RunScript(f"drawCRSBBox({crs_bbox_feature})")


    def on_select(self, event):
        self.selected_crs = self.find_selected_crs()
        self.Destroy()


    def on_close(self, event):
        self.Destroy()


    #################################
    # Utilities
    def switch_logical_operator(self, op):
        self.logical_buttons[op].SetValue(True)
        self.logical_operator = op
        self.query(self.create_parsable_geoms())
        if DEBUG:
            ppik.message(f"Logical operator: {self.logical_operator}")


    def create_parsable_geoms(self):
        # When switching logical operators and no geometry is drawn
        if self.json is None:
            return None

        geoms = self.logical_operator
        for feature in self.json["features"]:
            json_geom = feature["geometry"]
            geom_type = json_geom["type"]
            coors = json_geom["coordinates"]
            geom = Geometry(json_geom["type"], json_geom["coordinates"])
            geoms += f"\n{geom.type}"
            if geom.type == "point":
                geoms += f"\n{geom.coors[0]},{geom.coors[1]}"
            else:
                for coors in geom.coors:
                    geoms += f"\n{coors[0]},{coors[1]}"

        return geoms


    def query(self, geoms):
        if geoms is not None:
            parsed_geoms = ppik.parse_mixed_geoms(geoms)
            self.crs = ppik.query_mixed_geoms(parsed_geoms)

            if DEBUG:
                ppik.message(f"Query geometries: {parsed_geoms}")
                ppik.message(f"Number of queried CRSs: {len(self.crs)}")
        else:
            self.crs = None

        self.crs_list.DeleteAllItems()

        # Populate CRS list
        if self.crs is not None and len(self.crs) > 0:
            for crs in self.crs:
                self.crs_list.Append((crs.crs_name,
                                      f"{crs.crs_auth_name}:{crs.crs_code}"))


    def find_selected_crs(self):
        sel_crs = None
        sel_index = self.crs_list.GetFirstSelected()
        if self.crs is not None and sel_index >= 0:
            sel_crs = self.crs[sel_index]
        return sel_crs


    def get_crs_info(self, crs):
        if crs is None:
            # Return the number of lines in crs_info;
            # XXX: Tricky to count the number of lines in crs_info dynamically
            # because we use an f-string with a namedtuple and it's not a good
            # idea to eval() its template; Just update this number as needed
            # when adding or deleting lines to and from crs_info below
            return 8

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
        crs_info = crs_info.rstrip()
        return crs_info


    def create_geojson_feature(self, typ, coors):
        geojson_feature = {
            "type": "Feature",
            "geometry": {
                "type": typ,
                "coordinates": coors
            }
        }
        return geojson_feature


    def create_crs_bbox_feature(self, crs):
        s = crs.south_lat
        n = crs.north_lat
        w = crs.west_lon
        e = crs.east_lon
        coors = [[[w, n], [e, n], [e, s], [w, s]]]
        return self.create_geojson_feature("Polygon", coors)


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "-l", "--layout",
            choices=("big_list", "big_map"),
            default="big_list",
            help="select the layout (default: big_list)")
    parser.add_argument(
            "geometry",
            nargs="*",
            help="query geometry in latitude and longitude (point or poly) or "
                "south, north, west, and east (bbox); each point or bbox is a "
                "separate argument and multiple polys are separated by any "
                "non-coordinate argument such as a comma")

    args = parser.parse_args()

    layout = args.layout
    geoms = args.geometry

    app = wx.App()
    ppik_gui = ProjPickerGUI(layout, geoms, None, title="ProjPicker GUI")
    app.MainLoop()
    ppik_gui.print_selected_crs_auth_code()


if __name__ == "__main__":
    sys.exit(main())
