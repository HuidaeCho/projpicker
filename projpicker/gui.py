"""
This module implements the GUI of ProjPicker.
"""

import re
import tkinter as tk
from tkinter import ttk

# https://stackoverflow.com/a/49480246/16079666
if __package__:
    from .openstreetmap import OpenStreetMap
    from . import projpicker as ppik
else:
    from openstreetmap import OpenStreetMap
    import projpicker as ppik


def start(bbox=[], single=False, crs_info_func=None):
    """
    Return selected BBox instances. If single is True, it returns a single BBox
    instance in a list.

    Args:
        bbox (list): Queried BBox instances. Defaults to [].
        single (bool): Whether or not a single BBox instance is returned.
            Defaults to False.
        crs_info_func (function): User function used for formatting CRS info.
            Defaults to None in which case the default function is provided.

    Returns:
        list: List of selected BBox instances.
    """
    sel_crs = []
    prev_crs_items = []
    all_proj_tables = "all proj_tables"
    all_units = "all units"
    tag_map = "map"
    tag_bbox = "bbox"
    tag_coor = "coor"
    zoomer = None
    bbox_latlon = []


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


    def draw_bbox():
        map_canvas.delete(tag_bbox)
        for xy in osm.get_xy(bbox_latlon):
            drawn_crs = map_canvas.create_rectangle(xy, tag=tag_bbox,
                                                    outline="red", width=2,
                                                    fill="red",
                                                    stipple="gray12")


    def zoom_map(x, y, dz):
        def zoom(x, y, dz):
            if osm.zoom(x, y, dz):
                draw_bbox()


        # https://stackoverflow.com/a/63305873/16079666
        # https://stackoverflow.com/a/26703844/16079666
        # https://wiki.tcl-lang.org/page/Tcl+event+loop
        # XXX: I tried multi-threading in the OpenStreetMap class, but
        # map_canvas flickered too much; according to the above references,
        # tkinter doesn't like threading, so I decided to use its native
        # after() and after_cancel() to keep only the last zooming event
        nonlocal zoomer

        if zoomer:
            map_canvas.after_cancel(zoomer)
        zoomer = map_canvas.after(0, zoom, x, y, dz)


    def on_drag(event):
        osm.drag(event.x, event.y)
        draw_bbox()


    def on_move(event):
        w = event.widget
        latlon = osm.canvas_to_latlon(event.x, event.y)
        w.delete(tag_coor)
        t = w.create_text(w.winfo_width(), w.winfo_height(), anchor=tk.SE,
                          text=f" {latlon[0]:.2f}, {latlon[1]:.2f} ",
                          tag=tag_coor)
        r = w.create_rectangle(w.bbox(t), outline="white", fill="white",
                               tag=tag_coor)
        w.tag_lower(r, t)


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
        bbox_latlon.clear()
        if curr_crs_item:
            crs = w.item(curr_crs_item)["values"][1]
            b = find_bbox(crs)
            crs_info = create_crs_info(b)
            crs_text.insert(tk.END, crs_info)

            s, n, w, e = b.south_lat, b.north_lat, b.west_lon, b.east_lon
            s, n, w, e = osm.zoom_to_bbox([s, n, w, e])
            bbox_latlon.extend([[n, w], [s, e]])

            crs_info_query_notebook.select(crs_info_frame)

        draw_bbox()


    def on_select_proj_table_or_unit(event):
        proj_table = projection_types[proj_table_combobox.current()]
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


    def populate_crs_list(bbox):
        crs_treeview.delete(*crs_treeview.get_children())
        for b in bbox:
            crs_treeview.insert("", tk.END, values=(
                                b.crs_name, f"{b.crs_auth_name}:{b.crs_code}"))


    def select():
        nonlocal sel_crs

        for item in crs_treeview.selection():
            sel_crs.append(crs_treeview.item(item)["values"][1])
        root.destroy()


    def query():
        nonlocal bbox

        geoms = query_text.get("1.0", tk.END)
        bbox = ppik.query_mixed_geoms(geoms)
        populate_crs_list(bbox)


    lat = 0
    lon = 0
    zoom = 0

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
                                        tag=tag_map))

    osm.set_map_size(map_canvas_width, map_canvas_height)
    osm.draw_map(lat, lon, zoom)

    map_canvas.bind("<Button-1>", lambda e: osm.start_dragging(e.x, e.y))
    map_canvas.bind("<B1-Motion>", on_drag)
    # Linux
    # https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/event-types.html
    map_canvas.bind("<Button-4>", lambda e: zoom_map(e.x, e.y, 1))
    map_canvas.bind("<Button-5>", lambda e: zoom_map(e.x, e.y, -1))
    # Windows and macOS
    # https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/event-types.html
    map_canvas.bind("<MouseWheel>",
                    lambda e: zoom_map(e.x, e.y, 1 if e.delta > 0 else -1))
    map_canvas.bind("<Motion>", on_move)

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

    # list box for projection types
    projection_types = [all_proj_tables]
    projection_types.extend(sorted(set([b.proj_table for b in bbox])))

    proj_table_combobox = ttk.Combobox(bottom_left_bottom_frame, width=10)
    proj_table_combobox["values"] = projection_types
    proj_table_combobox.set(all_proj_tables)
    # bind selection event to run on select
    proj_table_combobox.bind("<<ComboboxSelected>>",
                             on_select_proj_table_or_unit)
    proj_table_combobox.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

    # list of units
    units = [all_units]
    units.extend(sorted(set([b.unit for b in bbox])))

    unit_combobox = ttk.Combobox(bottom_left_bottom_frame, width=10)
    unit_combobox["values"] = units
    unit_combobox.set(all_units)
    # bind selection event to run on select
    unit_combobox.bind("<<ComboboxSelected>>", on_select_proj_table_or_unit)
    unit_combobox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    ####################
    # bottom-right frame
    crs_info_query_notebook_width = root_width - bottom_left_frame_width
    crs_info_query_notebook = ttk.Notebook(bottom_frame,
                                         width=crs_info_query_notebook_width)
    crs_info_query_notebook.pack_propagate(False)

    crs_info_frame = tk.Frame(crs_info_query_notebook)
    crs_info_query_notebook.add(crs_info_frame, text="CRS Info")

    query_frame = tk.Frame(crs_info_query_notebook)
    crs_info_query_notebook.add(query_frame, text="Query")

    crs_info_query_notebook.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    ################
    # CRS info frame

    # text for CRS info
    crs_text = tk.Text(crs_info_frame, width=20, height=1, wrap=tk.NONE)
    crs_text.insert(tk.END, "Select a CRS from the left pane.")
    crs_text.bind("<Key>", lambda e: "break" if e.state == 0 else None)
    crs_text.pack(fill=tk.BOTH, expand=True)

    # horizontal scroll bar for CRS info
    crs_info_hscrollbar = tk.Scrollbar(crs_info_frame, orient=tk.HORIZONTAL)
    crs_info_hscrollbar.config(command=crs_text.xview)
    crs_info_hscrollbar.pack(fill=tk.X)
    crs_text.config(xscrollcommand=crs_info_hscrollbar.set)

    crs_info_buttons_frame = tk.Frame(crs_info_frame)
    crs_info_buttons_frame.pack(fill=tk.BOTH)

    # buttons
    tk.Button(crs_info_buttons_frame, text="Select", command=select).pack(
            side=tk.LEFT, expand=True)
    tk.Button(crs_info_buttons_frame, text="Cancel", command=root.destroy).pack(
            side=tk.LEFT, expand=True)

    #############
    # query frame
    query_top_frame = tk.Frame(query_frame)
    query_top_frame.pack(fill=tk.BOTH, expand=True)

    # text for query
    query_text = tk.Text(query_top_frame, width=20, height=1, wrap=tk.NONE)
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

    query_buttons_frame = tk.Frame(query_frame)
    query_buttons_frame.pack(fill=tk.BOTH)

    # buttons
    tk.Button(query_buttons_frame, text="Query", command=query).pack(
            side=tk.LEFT, expand=True)
    tk.Button(query_buttons_frame, text="Cancel", command=root.destroy).pack(
            side=tk.LEFT, expand=True)

    #########
    # run GUI
    root.mainloop()

    return [find_bbox(crs) for crs in sel_crs]
