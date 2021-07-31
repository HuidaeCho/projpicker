"""
This module implements the ProjPicker GUI using wxPython.
"""

import wx.lib.statbmp
import io
import threading
import queue
import textwrap
import webbrowser

# https://stackoverflow.com/a/49480246/16079666
if __package__:
    from .getosm import OpenStreetMap
    from . import projpicker as ppik
    from .gui_common import (get_lat, get_lon, get_zoom, get_dzoom,
                             parse_geoms, adjust_lon, calc_geoms_bbox,
                             create_crs_info, find_bbox)
else:
    from getosm import OpenStreetMap
    import projpicker as ppik
    from gui_common import (get_lat, get_lon, get_zoom, get_dzoom, parse_geoms,
                            adjust_lon, calc_geoms_bbox, create_crs_info,
                            find_bbox)


def start(
        geoms=None,
        bbox=[],
        bbox_or_quit=False,
        single=False,
        format_crs_info=None,
        projpicker_db=None):
    """
    Start the GUI. Parsable geometries by geoms or queried BBox instances by
    bbox can be specified optionally. If both are given, bbox is ignored and
    only geoms is used. If single is True, it returns a single BBox instance in
    a list.

    Args:
        geoms (list or str): Parsable geometries. Defaults to None.
        bbox (list): Queried BBox instances. Defaults to [].
        bbox_or_quit (bool): Whether or not to quit when bbox queried using
            input geoms or input bbox is empty. Defaults to False.
        single (bool): Whether or not a single BBox instance is returned.
            Defaults to False.
        format_crs_info (function): User function used for formatting CRS info.
            Defaults to None in which case the default function is provided.
        projpicker_db (str): projpicker.db path. Defaults to None.

    Returns:
        list, list, list: Lists of selected BBox instances, queried BBox
        instances sorted by area, and parsed geometries.
    """
    sel_crs = []
    prev_crs_items = []
    sel_bbox = []

    proj_tables = []
    units = []
    all_proj_tables = "all proj_tables"
    all_units = "all units"

    doc_url = "https://projpicker.readthedocs.io/"

    zoomer = None
    zoomer_queue = queue.Queue()
    dzoom = get_dzoom()

    dragged = False
    dragging_bbox = False
    dragged_bbox = []
    drawing_bbox = False
    complete_drawing = False
    prev_xy = []
    curr_geom = []
    all_geoms = []

    point_size = 4
    line_width = 2
    fill_alpha = 50
    geoms_color = "blue"
    dragged_bbox_color = "green"
    sel_bbox_color = "red"

    lat = get_lat()
    lon = get_lon()
    zoom = get_zoom()

    def draw_map(x, y):
        osm.draw()
        draw_geoms(x, y)

    def draw_geoms(x=None, y=None):
        all_geoms.clear()
        all_geoms.extend(geoms)
        if curr_geom and x and y:
            latlon = list(osm.canvas_to_latlon(x, y))

            g = curr_geom.copy()
            g.append(latlon)

            if drawing_bbox:
                ng = len(g)
                if ng > 0:
                    s = min(g[0][0], g[ng-1][0])
                    n = max(g[0][0], g[ng-1][0])
                    w = g[0][1]
                    e = g[ng-1][1]
                    if s == n:
                        n += 0.0001
                    if w == e:
                        e += 0.0001
                    all_geoms.extend(["bbox", [s, n, w, e]])
            elif g:
                if prev_xy:
                    latlon[1] = adjust_lon(prev_xy[0], x,
                                           curr_geom[len(curr_geom)-1][1],
                                           latlon[1])
                g.append(latlon)
                all_geoms.extend(["poly", g])

        map_canvas.Refresh()

    def on_grab(event):
        osm.grab(event.x, event.y)

    def on_draw(event):
        nonlocal dragged, dragging_bbox, drawing_bbox, complete_drawing

        if dragging_bbox:
            ng = len(dragged_bbox)
            s = min(dragged_bbox[0][0], dragged_bbox[ng-1][0])
            n = max(dragged_bbox[0][0], dragged_bbox[ng-1][0])
            w = dragged_bbox[0][1]
            e = dragged_bbox[ng-1][1]
            if s == n:
                n += 0.0001
            if w == e:
                e += 0.0001
            osm.zoom_to_bbox([s, n, w, e], False)
            dragged_bbox.clear()
            dragging_bbox = False
            draw_map(event.x, event.y)
        elif complete_drawing:
            query = ""
            geom = []
            if drawing_bbox:
                if len(curr_geom) == 2:
                    s = min(curr_geom[0][0], curr_geom[1][0])
                    n = max(curr_geom[0][0], curr_geom[1][0])
                    w = curr_geom[0][1]
                    e = curr_geom[1][1]
                    geom.extend(["bbox", [s, n, w, e]])
                    query = f"bbox {s:.4f},{n:.4f},{w:.4f},{e:.4f}"
                drawing_bbox = False
            elif len(curr_geom) == 1:
                lat, lon = curr_geom[0]
                geom.extend(["point", [lat, lon]])
                query = f"point {lat:.4f},{lon:.4f}"
            elif curr_geom:
                geom.extend(["poly", curr_geom.copy()])
                query = "poly"
                for g in curr_geom:
                    lat, lon = g
                    query += f" {lat:.4f},{lon:.4f}"
            geoms.extend(geom)
            curr_geom.clear()
            prev_xy.clear()
            if query:
                query += "\n"
                sel = query_text.GetSelection()
                if sel[0] > 0 and query_text.GetValue()[sel[0] - 1] != "\n":
                    query = "\n" + query
                query_text.Replace(sel[0], sel[1], query)
                bottom_right_notebook.ChangeSelection(query_panel.page)
                draw_geoms()
        elif not dragged:
            if event.ControlDown():
                drawing_bbox = True
                curr_geom.clear()
            elif drawing_bbox and len(curr_geom) == 2:
                del curr_geom[1]
            latlon = list(osm.canvas_to_latlon(event.x, event.y))
            if not drawing_bbox:
                if prev_xy:
                    latlon[1] = adjust_lon(prev_xy[0], event.x,
                                           curr_geom[len(curr_geom)-1][1],
                                           latlon[1])
                prev_xy.clear()
                prev_xy.extend([event.x, event.y])
            curr_geom.append(latlon)

        dragged = False
        complete_drawing = False

    def on_complete_drawing(event):
        nonlocal complete_drawing

        complete_drawing = True

    def on_cancel_drawing(event):
        nonlocal drawing_bbox

        drawing_bbox = False
        curr_geom.clear()
        prev_xy.clear()
        draw_geoms()

    def on_clear_drawing(event):
        query_text.Clear()
        geoms.clear()

    def on_move(event):
        nonlocal dragged, dragging_bbox

        if event.ControlDown() and event.LeftIsDown() and event.Dragging():
            latlon = osm.canvas_to_latlon(event.x, event.y)
            if not dragging_bbox:
                dragging_bbox = True
                dragged_bbox.append(latlon)
            else:
                if len(dragged_bbox) == 2:
                    del dragged_bbox[1]
                dragged_bbox.append(latlon)
                map_canvas.Refresh()
        elif event.LeftIsDown() and event.Dragging():
            osm.drag(event.x, event.y)
            dragged = True
        else:
            latlon = osm.canvas_to_latlon(event.x, event.y)
            coor_label.SetLabel(f"{latlon[0]:.4f}, {latlon[1]:.4f} ")
            main_box.Layout()
            draw_map(event.x, event.y)

    def on_zoom(event):
        def zoom(x, y, dz, cancel_event):
            if not cancel_event.wait(0.01) and osm.redownload():
                zoomer_queue.put(osm.draw)

        def check_zoomer():
            nonlocal zoomer

            try:
                draw_map = zoomer_queue.get_nowait()
            except:
                zoomer.checker = wx.CallLater(0, check_zoomer)
            else:
                draw_map()

        nonlocal zoomer

        dz = event.WheelRotation / event.WheelDelta * dzoom

        if event.ControlDown():
            if dz > 0:
                geoms_bbox = calc_geoms_bbox()
                if None not in geoms_bbox:
                    osm.zoom_to_bbox(geoms_bbox, False)
            else:
                osm.zoom(event.x, event.y, osm.z_min - osm.z, False)
            draw_map(event.x, event.y)
            return

        if zoomer:
            zoomer.cancel_event.set()
            osm.cancel = True
            zoomer.join()
            osm.cancel = False
            zoomer.checker.Stop()

            cancel_event = zoomer.cancel_event
            cancel_event.clear()
        else:
            cancel_event = threading.Event()

        # if used without osm.draw(), it works; otherwise, only osm.draw()
        # is visible; timing?
        osm.rescale(event.x, event.y, dz)
        zoomer = threading.Thread(target=zoom, args=(event.x, event.y, dz,
                                                     cancel_event))
        zoomer.cancel_event = cancel_event
        zoomer.checker = wx.CallLater(0, check_zoomer)
        zoomer.start()

    def on_paint(event):
        def set_pen_brush(color):
            outline = wx.Colour(color)
            fill = wx.Colour(outline.Red(), outline.Green(), outline.Blue(),
                             fill_alpha)

            dc.SetPen(wx.Pen(outline, width=line_width))

            # not all platforms support alpha?
            # https://wxpython.org/Phoenix/docs/html/wx.Colour.html#wx.Colour.Alpha
            if fill.Alpha() == wx.ALPHA_OPAQUE:
                dc.SetBrush(wx.Brush(fill, wx.BRUSHSTYLE_TRANSPARENT))
            else:
                dc.SetBrush(wx.Brush(fill))

        point_half_size = point_size // 2

        map_canvas.OnPaint(event)
        dc = wx.PaintDC(map_canvas)

        set_pen_brush(geoms_color)

        geom_type = "point"
        g = 0
        ngeoms = len(all_geoms)
        while g < ngeoms:
            geom = all_geoms[g]
            if geom in ("point", "poly", "bbox"):
                geom_type = geom
                g += 1
                geom = all_geoms[g]
            if type(geom) == list:
                if geom_type == "point":
                    for xy in osm.get_xy([geom]):
                        dc.DrawCircle(*xy[0], point_half_size)
                elif geom_type == "poly":
                    for xy in osm.get_xy(geom):
                        dc.DrawPolygon(xy)
                else:
                    for xy in osm.get_bbox_xy(geom):
                        x, y = xy[0]
                        w, h = xy[1][0] - x, xy[1][1] - y
                        dc.DrawRectangle(x, y, w, h)
            g += 1

        if dragged_bbox:
            set_pen_brush(dragged_bbox_color)

            ng = len(dragged_bbox)
            s = dragged_bbox[ng-1][0]
            n = dragged_bbox[0][0]
            w = dragged_bbox[0][1]
            e = dragged_bbox[ng-1][1]

            for xy in osm.get_bbox_xy((s, n, w, e)):
                x, y = xy[0]
                w, h = xy[1][0] - x, xy[1][1] - y
                dc.DrawRectangle(x, y, w, h)

        if sel_bbox:
            set_pen_brush(sel_bbox_color)

            for xy in osm.get_bbox_xy(sel_bbox):
                x, y = xy[0]
                w, h = xy[1][0] - x, xy[1][1] - y
                dc.DrawRectangle(x, y, w, h)

    def on_select_crs(event):
        nonlocal prev_crs_items

        curr_crs_items = []
        item = crs_list.GetFirstSelected()
        while item != -1:
            curr_crs_items.append(item)
            item = crs_list.GetNextSelected(item)

        if single:
            prev_crs_items.clear()

        curr_crs_item = -1
        if len(curr_crs_items) > len(prev_crs_items):
            # selected a new crs
            curr_crs_item = list(set(curr_crs_items) - set(prev_crs_items))[0]
            prev_crs_items.append(curr_crs_item)
        elif len(curr_crs_items) < len(prev_crs_items):
            # deselected an existing crs
            item = list(set(prev_crs_items) - set(curr_crs_items))[0]
            del prev_crs_items[prev_crs_items.index(item)]
            l = len(prev_crs_items)
            if l > 0:
                curr_crs_item = prev_crs_items[l-1]
        elif curr_crs_items:
            prev_crs_items.clear()
            prev_crs_items.extend(curr_crs_items)
            curr_crs_item = prev_crs_items[len(prev_crs_items)-1]

        crs_info_text.Clear()
        sel_bbox.clear()
        if curr_crs_item >= 0:
            crs = crs_list.GetItemText(curr_crs_item, 1)
            b = find_bbox(crs, bbox)
            crs_info = create_crs_info(b, format_crs_info)
            crs_info_text.SetValue(crs_info)

            s, n, w, e = b.south_lat, b.north_lat, b.west_lon, b.east_lon
            s, n, w, e = osm.zoom_to_bbox([s, n, w, e])
            sel_bbox.extend([s, n, w, e])

            bottom_right_notebook.ChangeSelection(crs_info_panel.page)
        draw_geoms()

    def on_select_proj_table_or_unit(event):
        proj_table = proj_tables[proj_table_choice.GetSelection()]
        unit = units[unit_choice.GetSelection()]

        if proj_table == all_proj_tables and unit == all_units:
            filt_bbox = bbox
        elif proj_table == all_proj_tables:
            filt_bbox = filter(lambda b: b.unit==unit, bbox)
        elif unit == all_units:
            filt_bbox = filter(lambda b: b.proj_table==proj_table, bbox)
        else:
            filt_bbox = filter(lambda b: b.proj_table==proj_table and
                                         b.unit==unit, bbox)

        populate_crs_list(filt_bbox)
        prev_crs_items.clear()

    def import_query():
        with wx.FileDialog(query_text, "Import query", wildcard=file_types,
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fd:
            if fd.ShowModal() != wx.ID_CANCEL:
                try:
                    with open(fd.GetPath()) as f:
                        query_text.SetValue(f.read())
                        f.close()
                except Exception as e:
                    wx.MessageDialog(query_text, str(e),
                                     "Import query error").ShowModal()

    def export_query():
        with wx.FileDialog(query_text, "Export query", wildcard=file_types,
                           defaultFile="query",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fd:
            if fd.ShowModal() != wx.ID_CANCEL:
                query_to_export = query_text.GetValue()
                try:
                    with open(fd.GetPath(), "w") as f:
                        f.write(query_to_export)
                except Exception as e:
                    wx.MessageDialog(query_text, str(e),
                                     "Export query error").ShowModal()

    def query():
        nonlocal bbox

        query = query_text.GetValue()
        geoms.clear()
        try:
            geoms.extend(ppik.parse_mixed_geoms(query))
            bbox = ppik.query_mixed_geoms(geoms, projpicker_db)
        except Exception as e:
            log_text.SetValue(str(e))
            bottom_right_notebook.ChangeSelection(log_panel.page)
        else:
            log_text.SetValue("")

        populate_crs_list(bbox)
        populate_filters(bbox)
        draw_geoms()

    def populate_crs_list(bbox):
        crs_list.DeleteAllItems()
        for b in bbox:
            crs_list.Append((b.crs_name, f"{b.crs_auth_name}:{b.crs_code}"))
        sel_bbox.clear()

    def populate_filters(bbox):
        proj_tables.clear()
        proj_tables.append(all_proj_tables)
        proj_tables.extend(sorted(set([b.proj_table for b in bbox])))
        proj_table_choice.Clear()
        for proj_table in proj_tables:
            proj_table_choice.Append(proj_table)
        proj_table_choice.Select(0)

        units.clear()
        units.append(all_units)
        units.extend(sorted(set([b.unit for b in bbox])))
        unit_choice.Clear()
        for unit in units:
            unit_choice.Append(unit)
        unit_choice.Select(0)

    def select():
        nonlocal sel_crs

        item = crs_list.GetFirstSelected()
        while item != -1:
            sel_crs.append(crs_list.GetItemText(item, 1))
            item = crs_list.GetNextSelected(item)
        root.Close()

    # parse geometries if given
    geoms, query_string = parse_geoms(geoms)

    if bbox_or_quit and not bbox:
        return [], bbox, geoms

    #####
    # GUI

    # root window
    app = wx.App()
    root_width = 800
    root_height = root_width
    root_size = (root_width, root_height)
    root = wx.Frame(None, title="ProjPicker wxGUI", size=root_size)
    main_box = wx.BoxSizer(wx.VERTICAL)

    ###########
    # top frame
    map_canvas_width = root_width
    map_canvas_height = root_height // 2
    map_canvas_size = (map_canvas_width, map_canvas_height)

    map_canvas = wx.lib.statbmp.GenStaticBitmap(root, wx.ID_ANY, wx.NullBitmap,
                                                size=map_canvas_size)

    osm = OpenStreetMap(
            wx.Image,
            lambda image: map_canvas.SetBitmap(wx.Bitmap(image)),
            lambda data: wx.Image(io.BytesIO(data)),
            lambda image, tile, x, y: image.Paste(tile, x, y),
            lambda tile, dz: tile.Scale(tile.Width*2**dz, tile.Height*2**dz),
            map_canvas.Size.Width, map_canvas.Size.Height,
            lat, lon, zoom)

    map_canvas.Bind(wx.EVT_LEFT_DOWN, on_grab)
    map_canvas.Bind(wx.EVT_LEFT_UP, on_draw)
    map_canvas.Bind(wx.EVT_LEFT_DCLICK, on_complete_drawing)
    map_canvas.Bind(wx.EVT_RIGHT_UP, on_cancel_drawing)
    map_canvas.Bind(wx.EVT_RIGHT_DCLICK, on_clear_drawing)
    map_canvas.Bind(wx.EVT_MOTION, on_move)
    map_canvas.Bind(wx.EVT_MOUSEWHEEL, on_zoom)
    map_canvas.Bind(wx.EVT_SIZE, lambda e: osm.resize(e.Size.Width,
                                                      e.Size.Height))
    map_canvas.Bind(wx.EVT_PAINT, on_paint)
    main_box.Add(map_canvas)

    # draw geometries if given
    if geoms:
        geoms_bbox = calc_geoms_bbox()
        if None not in geoms_bbox:
            osm.zoom_to_bbox(geoms_bbox)
        draw_geoms()

    #######################
    # label for coordinates
    coor_label = wx.StaticText(root)
    main_box.Add(coor_label, 0, wx.ALIGN_RIGHT)

    ##############
    # bottom frame
    bottom_box = wx.BoxSizer(wx.HORIZONTAL)

    ###################
    # bottom-left frame
    bottom_left_box = wx.BoxSizer(wx.VERTICAL)

    #######################
    # bottom-left-top frame

    # list of CRSs
    crs_list_width = root_width // 2
    crs_list_height = root_height - map_canvas_height - 45
    crs_list_size = (crs_list_width, crs_list_height)
    crs_list = wx.ListCtrl(root, size=crs_list_size, style=wx.LC_REPORT)

    code_width = 150
    name_width = crs_list_width - code_width
    crs_list.AppendColumn("Name", width=name_width)
    crs_list.AppendColumn("Code", width=code_width)
    bottom_left_box.Add(crs_list)

    populate_crs_list(bbox)

    crs_list.Bind(wx.EVT_LIST_ITEM_SELECTED, on_select_crs)
    crs_list.Bind(wx.EVT_LIST_ITEM_DESELECTED, on_select_crs)

    ##########################
    # bottom-left-bottom frame
    bottom_left_bottom_box = wx.BoxSizer(wx.HORIZONTAL)

    proj_table_choice = wx.Choice(root, size=(crs_list_width // 2, 30))
    proj_table_choice.Bind(wx.EVT_CHOICE, on_select_proj_table_or_unit)

    unit_choice = wx.Choice(root, size=(crs_list_width // 2, 30))
    unit_choice.Bind(wx.EVT_CHOICE, on_select_proj_table_or_unit)

    populate_filters(bbox)

    bottom_left_bottom_box.Add(proj_table_choice)
    bottom_left_bottom_box.Add(unit_choice)
    bottom_left_box.Add(bottom_left_bottom_box)
    bottom_box.Add(bottom_left_box)

    ####################
    # bottom-right frame
    bottom_right_notebook_width = root_width - crs_list_width
    bottom_right_notebook_height = root_height - map_canvas_height
    bottom_right_notebook = wx.Notebook(root)

    query_panel = wx.Panel(bottom_right_notebook)
    query_panel.page = bottom_right_notebook.GetPageCount()
    bottom_right_notebook.AddPage(query_panel, "Query")

    crs_info_panel = wx.Panel(bottom_right_notebook)
    crs_info_panel.page = bottom_right_notebook.GetPageCount()
    bottom_right_notebook.AddPage(crs_info_panel, "CRS Info")

    log_panel = wx.Panel(bottom_right_notebook)
    log_panel.page = bottom_right_notebook.GetPageCount()
    bottom_right_notebook.AddPage(log_panel, "Log")

    help_panel = wx.Panel(bottom_right_notebook)
    help_panel.page = bottom_right_notebook.GetPageCount()
    bottom_right_notebook.AddPage(help_panel, "Help")

    #############
    # query panel
    query_box = wx.BoxSizer(wx.VERTICAL)

    # text for query
    query_text = wx.TextCtrl(query_panel, style=wx.TE_MULTILINE | wx.HSCROLL,
                             size=(bottom_right_notebook_width,
                                   bottom_right_notebook_height - 75))
    # https://dzone.com/articles/wxpython-learning-use-fonts
    query_text.SetFont(wx.Font(9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,
                               wx.FONTWEIGHT_NORMAL))
    query_box.Add(query_text)

    # pop-up menu
    menu = wx.Menu()
    import_menuitem = wx.MenuItem(menu, wx.NewId(), "Import query")
    export_menuitem = wx.MenuItem(menu, wx.NewId(), "Export query")
    menu.Append(import_menuitem)
    menu.Append(export_menuitem)

    file_types = "ProjPicker query files (*.ppik)|*.ppik|All files (*.*)|*.*"
    query_text.Bind(wx.EVT_MENU, lambda e: import_query(), import_menuitem)
    query_text.Bind(wx.EVT_MENU, lambda e: export_query(), export_menuitem)

    query_text.Bind(wx.EVT_RIGHT_DOWN,
                    lambda e: query_text.PopupMenu(menu, e.GetPosition()))

    # buttons
    query_button = wx.Button(query_panel, label="Query")
    query_button.Bind(wx.EVT_BUTTON, lambda e: query())

    cancel_button = wx.Button(query_panel, label="Cancel")
    cancel_button.Bind(wx.EVT_BUTTON, lambda e: root.Close())

    query_bottom_box = wx.BoxSizer(wx.HORIZONTAL)
    query_bottom_box.Add(query_button, 1)
    query_bottom_box.AddStretchSpacer()
    query_bottom_box.Add(cancel_button, 1)
    query_box.Add(query_bottom_box, 0, wx.ALIGN_CENTER)
    query_panel.SetSizer(query_box)

    ################
    # CRS info panel
    crs_info_box = wx.BoxSizer(wx.VERTICAL)

    # text for CRS info
    crs_info_text = wx.TextCtrl(
            crs_info_panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL,
            size=(bottom_right_notebook_width,
                  bottom_right_notebook_height - 75))
    # https://dzone.com/articles/wxpython-learning-use-fonts
    crs_info_text.SetFont(query_text.GetFont())
    crs_info_box.Add(crs_info_text)

    # buttons
    select_button = wx.Button(crs_info_panel, label="Select")
    select_button.Bind(wx.EVT_BUTTON, lambda e: select())

    cancel_button = wx.Button(crs_info_panel, label="Cancel")
    cancel_button.Bind(wx.EVT_BUTTON, lambda e: root.Close())

    crs_info_bottom_box = wx.BoxSizer(wx.HORIZONTAL)
    crs_info_bottom_box.Add(select_button, 1)
    crs_info_bottom_box.AddStretchSpacer()
    crs_info_bottom_box.Add(cancel_button, 1)
    crs_info_box.Add(crs_info_bottom_box, 0, wx.ALIGN_CENTER)
    crs_info_panel.SetSizer(crs_info_box)

    ###########
    # log panel

    # text for CRS info
    log_text = wx.TextCtrl(
            log_panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL,
            size=(bottom_right_notebook_width,
                  bottom_right_notebook_height - 45))
    # https://dzone.com/articles/wxpython-learning-use-fonts
    log_text.SetFont(query_text.GetFont())

    ############
    # help panel

    # text for help
    help_text = wx.TextCtrl(
            help_panel, value=textwrap.dedent(f"""\
            Map operations
            ==============
            Pan:                        Left drag
            Zoom:                       Scroll
            Zoom to geometries:         Ctrl + scroll up
            Zoom to the world:          Ctrl + scroll down
            Draw/zoom to a bbox:        Ctrl + left drag
            Draw a point:               Double left click
            Start drawing a poly:       Left click
            Start drawing a bbox:       Ctrl + left click
            Complete a poly/bbox:       Double left click
            Cancel drawing a poly/bbox: Right click
            Clear geometries:           Double right click

            Geometry variables
            ==================
            To define a geometry variable, type and highlight
            a name in the query builder, then create a geometry.

            Query import & export
            =====================
            Query files (*.ppik) can be imported or exported
            by right clicking on the query builder.

            See {doc_url} to learn more."""),
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_AUTO_URL,
            size=(bottom_right_notebook_width,
                  bottom_right_notebook_height - 45))
    help_text.Bind(wx.EVT_TEXT_URL,
                   lambda e: webbrowser.open(github_url)
                             if e.GetMouseEvent().LeftIsDown() else None)
    help_text.SetFont(query_text.GetFont())

    bottom_box.Add(bottom_right_notebook)
    main_box.Add(bottom_box)

    root.SetSizer(main_box)

    #########
    # run GUI
    root.Show()
    app.MainLoop()

    return [find_bbox(crs, bbox) for crs in sel_crs], bbox, geoms
