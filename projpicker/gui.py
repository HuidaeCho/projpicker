"""
This module implements the GUI of ProjPicker.
"""

import tkinter as tk
from tkinter import ttk
import textwrap
import webbrowser

# https://stackoverflow.com/a/49480246/16079666
if __package__:
    from .getosm import OpenStreetMap
    from . import projpicker as ppik
else:
    from getosm import OpenStreetMap
    import projpicker as ppik


def start(
        geoms=None,
        bbox=[],
        single=False,
        crs_info_func=None,
        projpicker_db=None):
    """
    Start the GUI. Parsable geometries by geoms or queried BBox instances by
    bbox can be specified optionally. If both are given, bbox is ignored and
    only geoms is used. If single is True, it returns a single BBox instance in
    a list.

    Args:
        geoms (list or str): Parsable geometries. Defaults to None.
        bbox (list): Queried BBox instances. Defaults to [].
        single (bool): Whether or not a single BBox instance is returned.
            Defaults to False.
        crs_info_func (function): User function used for formatting CRS info.
            Defaults to None in which case the default function is provided.
        projpicker_db (str): projpicker.db path. Defaults to None.

    Returns:
        list, list, list: Lists of selected BBox instances, queried BBox
        instances sorted by area, and parsed geometries.
    """
    sel_crs = []
    prev_crs_items = []
    all_proj_tables = "all proj_tables"
    all_units = "all units"
    tag_map = "map"
    tag_bbox = "bbox"
    tag_geoms = "geoms"
    tag_doc = "doc"
    doc_url = "https://projpicker.readthedocs.io/"
    zoomer = None
    dzoom = 1
    dragged = False
    drawing_bbox = False
    complete_drawing = False
    sel_bbox = []
    prev_xy = []
    curr_geom = []
    proj_tables = []
    units = []

    def adjust_lon(prev_x, x, prev_lon, lon):
        dlon = lon - prev_lon
        if x - prev_x > 0:
            if dlon < 0:
                lon += 360
            elif dlon > 360:
                lon -= 360
        elif dlon > 0:
            lon -= 360
        elif dlon < -360:
            lon += 360
        return lon

    def calc_geoms_bbox():
        s = n = w = e = None
        geom_type = "point"
        g = 0
        ngeoms = len(geoms)
        while g < ngeoms:
            geom = geoms[g]
            if geom in ("point", "poly", "bbox"):
                geom_type = geom
                g += 1
                geom = geoms[g]
            if type(geom) == list:
                if geom_type == "point":
                    lat, lon = geom
                    if s is None:
                        s = n = lat
                        w = e = lon
                    else:
                        if lat < s:
                            s = lat
                        elif lat > n:
                            n = lat
                        if lon < w:
                            w = lon
                        elif lon > e:
                            e = lon
                elif geom_type == "poly":
                    for coor in geom:
                        lat, lon = coor
                        if s is None:
                            s = n = lat
                            w = e = lon
                        else:
                            if lat < s:
                                s = lat
                            elif lat > n:
                                n = lat
                            if lon < w:
                                w = lon
                            elif lon > e:
                                e = lon
                else:
                    b, t, l, r = geom
                    if s is None:
                        s = b
                        n = t
                        w = l
                        e = r
                    else:
                        if b < s:
                            s = b
                        if t > n:
                            n = t
                        if l < w:
                            w = l
                        if r > e:
                            e = r
            g += 1
        if s == n:
            s -= 0.0001
            n += 0.0001
        if w == e:
            w -= 0.0001
            e += 0.0001
        return s, n, w, e

    def draw_geoms(x=None, y=None):
        point_size = 4
        point_half_size = point_size // 2
        outline = "blue"
        width = 2
        fill = "blue"
        stipple = "gray12"

        map_canvas.delete(tag_geoms)

        if curr_geom and x and y:
            latlon = list(osm.canvas_to_latlon(x, y))

            all_geoms = geoms.copy()
            g = curr_geom.copy()
            g.append(latlon)

            if drawing_bbox:
                ng = len(g)
                if ng > 0:
                    s = g[ng-1][0]
                    n = g[0][0]
                    w = g[0][1]
                    e = g[ng-1][1]
                    all_geoms.extend(["bbox", [s, n, w, e]])
            elif g:
                if prev_xy:
                    latlon[1] = adjust_lon(prev_xy[0], x,
                                           curr_geom[len(curr_geom)-1][1],
                                           latlon[1])
                g.append(latlon)
                all_geoms.extend(["poly", g])
        else:
            all_geoms = geoms.copy()

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
                        x, y = xy[0]
                        oval = (x - point_half_size, y - point_half_size,
                                x + point_half_size, y + point_half_size)
                        map_canvas.create_oval(oval, outline=outline,
                                               width=width, fill=fill,
                                               tag=tag_geoms)
                elif geom_type == "poly":
                    for xy in osm.get_xy(geom):
                        map_canvas.create_polygon(xy, outline=outline,
                                                  width=width, fill=fill,
                                                  stipple=stipple,
                                                  tag=tag_geoms)
                else:
                    for xy in osm.get_bbox_xy(geom):
                        map_canvas.create_rectangle(xy, outline=outline,
                                                    width=width, fill=fill,
                                                    stipple=stipple,
                                                    tag=tag_geoms)
            g += 1

    def draw_bbox():
        map_canvas.delete(tag_bbox)
        for xy in osm.get_bbox_xy(sel_bbox):
            map_canvas.create_rectangle(xy, outline="red", width=2, fill="red",
                                        stipple="gray12", tag=tag_bbox)

    def zoom_map(x, y, dz):
        def zoom(x, y, dz):
            if osm.zoom(x, y, dz):
                draw_geoms(x, y)
                draw_bbox()

        # https://stackoverflow.com/a/63305873/16079666
        # https://stackoverflow.com/a/26703844/16079666
        # https://wiki.tcl-lang.org/page/Tcl+event+loop
        # XXX: Cho tried multi-threading in the OpenStreetMap class, but
        # map_canvas flickered too much; according to the above references,
        # tkinter doesn't like threading, so he decided to use its native
        # after() and after_cancel() to keep only the last zooming event
        nonlocal zoomer

        if zoomer:
            map_canvas.after_cancel(zoomer)
        zoomer = map_canvas.after(0, zoom, x, y, dz)

    def query():
        nonlocal bbox

        query = query_text.get("1.0", tk.END)
        geoms.clear()
        log_text.delete("1.0", tk.END)
        try:
            geoms.extend(ppik.parse_mixed_geoms(query))
            bbox = ppik.query_mixed_geoms(geoms, projpicker_db)
        except Exception as e:
            log_text.insert(tk.END, e)
            bottom_right_notebook.select(log_frame)

        populate_crs_list(bbox)
        populate_filters(bbox)
        draw_geoms()

    def populate_crs_list(bbox):
        crs_treeview.delete(*crs_treeview.get_children())
        for b in bbox:
            crs_treeview.insert("", tk.END, values=(
                                b.crs_name, f"{b.crs_auth_name}:{b.crs_code}"))
        sel_bbox.clear()
        draw_bbox()

    def populate_filters(bbox):
        proj_tables.clear()
        proj_tables.append(all_proj_tables)
        proj_tables.extend(sorted(set([b.proj_table for b in bbox])))
        proj_table_combobox["values"] = proj_tables
        proj_table_combobox.set(all_proj_tables)

        units.clear()
        units.append(all_units)
        units.extend(sorted(set([b.unit for b in bbox])))
        unit_combobox["values"] = units
        unit_combobox.set(all_units)

    def create_crs_info(bbox):
        if crs_info_func is None:
            dic = bbox._asdict()
            l = 0
            for key in dic.keys():
                if len(key) > l:
                    l = len(key)
            l += 1
            txt = ""
            for key in dic.keys():
                k = key + ":"
                txt += f"{k:{l}} {dic[key]}\n"
        else:
            txt = crs_info_func(bbox)
        return txt

    def find_bbox(crs):
        if crs is None:
            return None

        auth, code = crs.split(":")
        b = list(filter(lambda b: b.crs_auth_name==auth and
                                  b.crs_code==code, bbox))[0]
        return b

    def select():
        nonlocal sel_crs

        for item in crs_treeview.selection():
            sel_crs.append(crs_treeview.item(item)["values"][1])
        root.destroy()

    def on_drag(event):
        nonlocal dragged

        osm.drag(event.x, event.y)
        draw_geoms(event.x, event.y)
        draw_bbox()
        dragged = True

    def on_move(event):
        latlon = osm.canvas_to_latlon(event.x, event.y)
        coor_label.config(text=f" {latlon[0]:.4f}, {latlon[1]:.4f} ")
        draw_geoms(event.x, event.y)

    def on_draw(event):
        nonlocal dragged, drawing_bbox, complete_drawing

        if complete_drawing:
            query = ""
            geom = []
            if drawing_bbox:
                if len(curr_geom) == 2:
                    s = curr_geom[1][0]
                    n = curr_geom[0][0]
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
                # https://stackoverflow.com/a/35855352/16079666
                # don't use .selection_get()
                ranges = query_text.tag_ranges(tk.SEL)
                if ranges:
                    name = query_text.get(*ranges).strip()
                    if not name.endswith(":"):
                        if not name.startswith(":"):
                            name = f":{name}:"
                        else:
                            name = ""
                    if name and ppik.geom_var_re.match(name):
                        query = query.replace(" ", f" {name} ")
                    index = ranges[0].string
                else:
                    index = query_text.index(tk.INSERT)
                line, col = list(map(lambda x: int(x), index.split(".")))
                if col > 0:
                    query = "\n" + query
                    line += 1
                if ranges:
                    query_text.replace(*ranges, query)
                else:
                    query_text.insert(tk.INSERT, query)
                query_text.mark_set(tk.INSERT, f"{line+1}.0")
                bottom_right_notebook.select(query_frame)
                draw_geoms()
        elif not dragged:
            # https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/event-handlers.html
            if event.state & 0x4:
                # Control + ButtonRelease-1
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

        # XXX: sometimes, double-click events occur for both clicks and there
        # is no reliable way to register the first click only using
        # complete_drawing; a hacky way to handle such cases
        if not curr_geom:
            curr_geom.append(osm.canvas_to_latlon(event.x, event.y))
            prev_xy = [event.x, event.y]
        complete_drawing = True

    def on_cancel_drawing(event):
        nonlocal drawing_bbox

        drawing_bbox = False
        curr_geom.clear()
        prev_xy.clear()
        draw_geoms()

    def on_select_crs(event):
        nonlocal prev_crs_items

        w = event.widget
        curr_crs_items = w.selection()

        if single:
            prev_crs_items.clear()

        curr_crs_item = None
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

        crs_text.delete("1.0", tk.END)
        sel_bbox.clear()
        if curr_crs_item:
            crs = w.item(curr_crs_item)["values"][1]
            b = find_bbox(crs)
            crs_info = create_crs_info(b)
            crs_text.insert(tk.END, crs_info)

            s, n, w, e = b.south_lat, b.north_lat, b.west_lon, b.east_lon
            s, n, w, e = osm.zoom_to_bbox([s, n, w, e])
            sel_bbox.extend([s, n, w, e])

            bottom_right_notebook.select(crs_info_frame)

        draw_geoms()
        draw_bbox()

    def on_select_proj_table_or_unit(event):
        proj_table = proj_tables[proj_table_combobox.current()]
        unit = units[unit_combobox.current()]

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

    lat = 0
    lon = 0
    zoom = 0

    # parse geometries if given
    query_string = ""
    if geoms:
        geoms = ppik.parse_mixed_geoms(geoms)
        geom_type = "point"
        for geom in geoms:
            if geom in ("point", "poly", "bbox"):
                line = geom_type = geom
            elif type(geom) == str:
                line = geom
            else:
                line = ""
                if geom_type == "poly":
                    for coor in geom:
                        line += (" " if line else "") + f"{coor[0]},{coor[1]}"
                else:
                    for coor in geom:
                        line += ("," if line else "") + f"{coor}"
            query_string += line + "\n"
        bbox = ppik.query_mixed_geoms(geoms, projpicker_db)
    else:
        geoms = []

    #####
    # GUI

    # root window
    root = tk.Tk()
    root_width = 800
    root_height = root_width
    root.geometry(f"{root_width}x{root_height}")
    root.resizable(False, False)
    root.title("ProjPicker GUI")
    # https://stackoverflow.com/a/5871414/16079666
    root.bind_class("Text", "<Control-a>",
                    lambda e: e.widget.tag_add(tk.SEL, "1.0", tk.END))

    ###########
    # top frame
    map_canvas_width = root_width
    map_canvas_height = root_height // 2

    map_canvas = tk.Canvas(root, height=map_canvas_height)
    map_canvas.pack(fill=tk.BOTH)

    osm = OpenStreetMap(
            lambda width, height: map_canvas.delete(tag_map),
            lambda image: map_canvas.tag_lower(tag_map),
            lambda data: tk.PhotoImage(data=data),
            lambda image, tile, x, y:
                map_canvas.create_image(x, y, anchor=tk.NW, image=tile,
                                        tag=tag_map),
            map_canvas_width, map_canvas_height,
            lat, lon, zoom)

    map_canvas.bind("<ButtonPress-1>", lambda e: osm.start_dragging(e.x, e.y))
    map_canvas.bind("<B1-Motion>", on_drag)
    map_canvas.bind("<ButtonRelease-1>", on_draw)
    map_canvas.bind("<Double-Button-1>", on_complete_drawing)
    map_canvas.bind("<ButtonRelease-3>", on_cancel_drawing)
    map_canvas.bind("<Double-Button-3>", lambda e: geoms.clear())
    # Linux
    # https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/event-types.html
    map_canvas.bind("<Button-4>", lambda e: zoom_map(e.x, e.y, dzoom))
    map_canvas.bind("<Button-5>", lambda e: zoom_map(e.x, e.y, -dzoom))
    # Windows and macOS
    # https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/event-types.html
    map_canvas.bind("<MouseWheel>",
                    lambda e: zoom_map(e.x, e.y,
                                       dzoom if e.delta > 0 else -dzoom))
    map_canvas.bind("<Motion>", on_move)

    # draw geometries if given
    if geoms:
        osm.zoom_to_bbox(calc_geoms_bbox())
        draw_geoms()

    ##############
    # bottom frame
    bottom_frame_height = root_height - map_canvas_height
    bottom_frame = tk.Frame(root, height=400)
    bottom_frame.pack_propagate(False)
    bottom_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    ###################
    # bottom-left frame
    bottom_left_frame_width = root_width // 2
    bottom_left_frame = tk.Frame(bottom_frame, width=bottom_left_frame_width)
    bottom_left_frame.pack_propagate(False)
    bottom_left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    #######################
    # bottom-left-top frame
    bottom_left_top_frame = tk.Frame(bottom_left_frame)
    bottom_left_top_frame.pack(fill=tk.BOTH, expand=True)

    # list of CRSs
    code_width = 100
    name_width = bottom_left_frame_width - code_width - 15
    crs_cols = {"Name": name_width, "Code": code_width}

    crs_treeview = ttk.Treeview(
            bottom_left_top_frame, columns=list(crs_cols.keys()),
            show="headings", selectmode=tk.BROWSE if single else tk.EXTENDED)
    for name, width in crs_cols.items():
        crs_treeview.heading(name, text=name)
        crs_treeview.column(name, width=width)

    populate_crs_list(bbox)

    crs_treeview.bind("<<TreeviewSelect>>", on_select_crs)
    crs_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # vertical scroll bar for CRS list
    crs_list_vscrollbar = tk.Scrollbar(bottom_left_top_frame)
    crs_list_vscrollbar.config(command=crs_treeview.yview)
    crs_list_vscrollbar.pack(side=tk.LEFT, fill=tk.Y)
    crs_treeview.config(yscrollcommand=crs_list_vscrollbar.set)

    ##########################
    # bottom-left-middle frame

    # horizontal scroll bar for CRS list
    crs_list_hscrollbar = tk.Scrollbar(bottom_left_frame,
                                   orient=tk.HORIZONTAL)
    crs_list_hscrollbar.config(command=crs_treeview.xview)
    crs_list_hscrollbar.pack(fill=tk.X)
    crs_treeview.config(xscrollcommand=crs_list_hscrollbar.set)

    ##########################
    # bottom-left-bottom frame
    bottom_left_bottom_frame = tk.Frame(bottom_left_frame)
    bottom_left_bottom_frame.pack(fill=tk.X, ipady=3, pady=2, padx=2)

    # list of proj_tables
    proj_table_combobox = ttk.Combobox(bottom_left_bottom_frame, width=10,
                                       state="readonly")
    proj_table_combobox.bind("<<ComboboxSelected>>",
                             on_select_proj_table_or_unit)
    proj_table_combobox.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

    # list of units
    unit_combobox = ttk.Combobox(bottom_left_bottom_frame, width=10,
                                 state="readonly")
    unit_combobox.bind("<<ComboboxSelected>>", on_select_proj_table_or_unit)
    unit_combobox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    populate_filters(bbox)

    ####################
    # bottom-right frame
    bottom_right_notebook_width = root_width - bottom_left_frame_width
    bottom_right_notebook = ttk.Notebook(bottom_frame,
                                         width=bottom_right_notebook_width)
    bottom_right_notebook.pack_propagate(False)

    query_frame = tk.Frame(bottom_right_notebook)
    bottom_right_notebook.add(query_frame, text="Query")

    crs_info_frame = tk.Frame(bottom_right_notebook)
    bottom_right_notebook.add(crs_info_frame, text="CRS Info")

    log_frame = tk.Frame(bottom_right_notebook)
    bottom_right_notebook.add(log_frame, text="Log")

    help_frame = tk.Frame(bottom_right_notebook)
    bottom_right_notebook.add(help_frame, text="Help")

    bottom_right_notebook.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    #############
    # query frame
    query_top_frame = tk.Frame(query_frame)
    query_top_frame.pack(fill=tk.BOTH, expand=True)

    # text for query
    query_text = tk.Text(query_top_frame, width=20, height=1, wrap=tk.NONE)
    query_text.insert(tk.INSERT, query_string)
    query_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # vertical scroll bar for query
    query_vscrollbar = tk.Scrollbar(query_top_frame)
    query_vscrollbar.config(command=query_text.yview)
    query_vscrollbar.pack(side=tk.LEFT, fill=tk.Y)
    query_text.config(yscrollcommand=query_vscrollbar.set)

    # horizontal scroll bar for query
    query_hscrollbar = tk.Scrollbar(query_frame, orient=tk.HORIZONTAL)
    query_hscrollbar.config(command=query_text.xview)
    query_hscrollbar.pack(fill=tk.X)
    query_text.config(xscrollcommand=query_hscrollbar.set)

    query_bottom_frame = tk.Frame(query_frame)
    query_bottom_frame.pack(fill=tk.BOTH)

    # buttons
    tk.Button(query_bottom_frame, text="Query", command=query).pack(
            side=tk.LEFT, expand=True)
    tk.Button(query_bottom_frame, text="Cancel", command=root.destroy).pack(
            side=tk.LEFT, expand=True)

    ################
    # CRS info frame

    # text for CRS info
    crs_text = tk.Text(crs_info_frame, width=20, height=1, wrap=tk.NONE)
    crs_text.bind("<Key>", lambda e: "break" if e.state == 0 else None)
    crs_text.pack(fill=tk.BOTH, expand=True)

    # horizontal scroll bar for CRS info
    crs_info_hscrollbar = tk.Scrollbar(crs_info_frame, orient=tk.HORIZONTAL)
    crs_info_hscrollbar.config(command=crs_text.xview)
    crs_info_hscrollbar.pack(fill=tk.X)
    crs_text.config(xscrollcommand=crs_info_hscrollbar.set)

    crs_info_bottom_frame = tk.Frame(crs_info_frame)
    crs_info_bottom_frame.pack(fill=tk.BOTH)

    # buttons
    tk.Button(crs_info_bottom_frame, text="Select", command=select).pack(
            side=tk.LEFT, expand=True)
    tk.Button(crs_info_bottom_frame, text="Cancel", command=root.destroy).pack(
            side=tk.LEFT, expand=True)

    ###########
    # log frame
    log_top_frame = tk.Frame(log_frame)
    log_top_frame.pack(fill=tk.BOTH, expand=True)

    # text for log
    log_text = tk.Text(log_top_frame, width=20, height=1, wrap=tk.NONE)
    log_text.bind("<Key>", lambda e: "break" if e.state == 0 else None)
    log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # vertical scroll bar for log
    log_vscrollbar = tk.Scrollbar(log_top_frame)
    log_vscrollbar.config(command=log_text.yview)
    log_vscrollbar.pack(side=tk.LEFT, fill=tk.Y)
    log_text.config(yscrollcommand=log_vscrollbar.set)

    # horizontal scroll bar for log
    log_hscrollbar = tk.Scrollbar(log_frame, orient=tk.HORIZONTAL)
    log_hscrollbar.config(command=log_text.xview)
    log_hscrollbar.pack(fill=tk.X)
    log_text.config(xscrollcommand=log_hscrollbar.set)

    ############
    # help frame

    # text for help
    help_text = tk.Text(help_frame, width=20, height=1, wrap=tk.NONE)
    help_text.insert(tk.END, textwrap.dedent(f"""\
            Map operations
            ==============
            Pan:                        Drag using left button
            Zoom:                       Scroll
            Draw point:                 Double left click
            Start drawing poly:         Left click
            Start drawing bbox:         Control + left click
            Complete drawing poly/bbox: Double left click
            Cancel drawing poly/bbox:   Right click
            Clear geometries:           Double right click

            Geometry variables
            ==================
            To define a geometry variable, type and highlight
            a name, then create a geometry.

            Documentation
            =============
            {doc_url}"""))
    help_text.tag_add(tag_doc, "end - 1 line", "end")
    help_text.tag_config(tag_doc, foreground="blue", underline=True)
    help_text.tag_bind(tag_doc, "<Enter>",
                       lambda e: help_text.config(cursor="hand2"))
    help_text.tag_bind(tag_doc, "<Leave>",
                       lambda e: help_text.config(cursor=""))
    help_text.tag_bind(tag_doc, "<Button-1>",
                       lambda e: webbrowser.open(doc_url))
    help_text.config(state=tk.DISABLED)
    help_text.pack(fill=tk.BOTH, expand=True)

    # label for coordinates
    coor_label = tk.Label(bottom_right_notebook)
    coor_label.place(relx=1, rely=0, anchor=tk.NE)

    #########
    # run GUI
    root.mainloop()

    return [find_bbox(crs) for crs in sel_crs], bbox, geoms
