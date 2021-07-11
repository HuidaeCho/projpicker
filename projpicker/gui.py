"""
This module implements the GUI of ProjPicker.
"""

import re
import tkinter as tk
from tkinter import ttk


def select_bbox(bbox, single=False, crs_info_func=None):
    """
    Return selected BBox instances. If single is True, it returns a single BBox
    instance in a list.

    Args:
        bbox (list): Queried BBox instances.
        single (bool): Whether or not a single BBox instance is returned.
            Defaults to False.
        crs_info_func (function): User function used for formatting CRS info.
            Defaults to None in which case the default function is provided.

    Returns:
        list: List of selected BBox instances.
    """
    sel_crs = []
    prev_crs_items = []

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


    def extract_crs_auth_code(sel):
        return re.sub("^.*\((.*)\)$", r"\1", sel)


    def find_bbox(crs):
        if crs is None:
            return None

        auth, code = crs.split(":")
        b = list(filter(lambda b: b.crs_auth_name==auth and
                                  b.crs_code==code, bbox))[0]
        return b


    def on_select_crs(event):
        nonlocal prev_crs_items

        w = event.widget
        curr_crs_items = w.selection()

        if single:
            prev_crs_items.clear()

        print("prev b", prev_crs_items)
        print("curr b", curr_crs_items)

        if len(curr_crs_items) > len(prev_crs_items):
            # selected a new crs
            curr_crs_item = list(set(curr_crs_items) - set(prev_crs_items))[0]
            prev_crs_items.append(curr_crs_item)
        elif len(curr_crs_items) < len(prev_crs_items):
            # deselected an existing crs
            curr_crs_item = list(set(prev_crs_items) - set(curr_crs_items))[0]
            del prev_crs_items[prev_crs_items.index(curr_crs_item)]
            l = len(prev_crs_items)
            if l > 0:
                curr_crs_item = prev_crs_items[l-1]
            else:
                curr_crs_item = None
        elif curr_crs_items:
            prev_crs_items.clear()
            prev_crs_items.extend(curr_crs_items)
            curr_crs_item = prev_crs_items[len(prev_crs_items)-1]
        else:
            curr_crs_item = None

        print("prev", prev_crs_items)
        print("curr", curr_crs_items)
        print("last", curr_crs_item)

        crs_text.delete("1.0", tk.END)
        if curr_crs_item:
            crs = w.item(curr_crs_item)["values"][1]
            crs_info = create_crs_info(find_bbox(crs))
            crs_text.insert(tk.END, crs_info)


    def on_select_proj_table_or_unit(event):
        proj_table_sel = proj_table_combobox.current()
        if proj_table_sel in (-1, 0):
            proj_table = "all"
        else:
            proj_table = projection_types[proj_table_sel]

        unit_sel = unit_combobox.current()
        if unit_sel in (-1, 0):
            unit = "all"
        else:
            unit = units[unit_sel]

        if proj_table == "all" and unit == "all":
            filt_bbox = bbox
        elif proj_table == "all":
            filt_bbox = filter(lambda b: b.unit==unit, bbox)
        elif unit == "all":
            filt_bbox = filter(lambda b: b.proj_table==proj_table, bbox)
        else:
            filt_bbox = filter(lambda b: b.proj_table==proj_table and
                                         b.unit==unit, bbox)

        crs_treeview.delete(0, tk.END)
        for b in filt_bbox:
            crs_treeview.insert(tk.END, f"{b.crs_name} "
                                       f"({b.crs_auth_name}:{b.crs_code})")
        prev_crs_items.clear()


    def select():
        nonlocal sel_crs

        for i in crs_treeview.curselection():
            sel_crs.append(extract_crs_auth_code(crs_treeview.get(i)))
        root.destroy()


    # root window
    root = tk.Tk()
    root_width = 800
    root_height = 800
    root.geometry(f"{root_width}x{root_height}")
    root.resizable(False, False)
    root.title("ProjPicker GUI")

    ############
    # left frame
    left_frame_width = root_width // 2
    left_frame = tk.Frame(bottom_frame, width=left_frame_width)
    left_frame.pack_propagate(False)
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    ################
    # left-top frame
    left_top_frame = tk.Frame(left_frame)
    left_top_frame.pack(fill=tk.BOTH, expand=True)

    # list of CRSs
    code_width = 100
    name_width = left_frame_width - code_width
    crs_cols = {"Name": name_width, "Code": code_width}

    crs_treeview = ttk.Treeview(
            left_top_frame, columns=list(crs_cols.keys()),
            show="headings", selectmode=tk.BROWSE if single else tk.EXTENDED)

    for name, width in crs_cols.items():
        print(name)
        crs_treeview.heading(name, text=name)
        crs_treeview.column(name, width=width)

    for b in bbox:
        crs_treeview.insert("", tk.END, values=(
                            b.crs_name, f"{b.crs_auth_name}:{b.crs_code}"))
    crs_treeview.bind("<<TreeviewSelect>>", on_select_crs)
    crs_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # vertical scroll bar for CRS list
    list_vscrollbar = tk.Scrollbar(left_top_frame)
    list_vscrollbar.config(command=crs_treeview.yview)
    list_vscrollbar.pack(side=tk.LEFT, fill=tk.BOTH)
    crs_treeview.config(yscrollcommand=list_vscrollbar.set)

    ################
    # left-middle frame
    left_middle_frame = tk.Frame(left_frame)
    left_middle_frame.pack(fill=tk.BOTH)

    # horizontal scroll bar for CRS list
    list_hscrollbar = tk.Scrollbar(left_middle_frame,
                                   orient=tk.HORIZONTAL)
    list_hscrollbar.config(command=crs_treeview.xview)
    list_hscrollbar.pack(side=tk.BOTTOM, fill=tk.BOTH)
    crs_treeview.config(xscrollcommand=list_hscrollbar.set)

    ###################
    # left-bottom frame
    left_bottom_frame = tk.Frame(left_frame)
    left_bottom_frame.pack(fill=tk.X, ipady=3, pady=2, padx=2)

    # list box for projection types
    projection_types = ["all"]
    projection_types.extend(sorted(set([b.proj_table for b in bbox])))

    proj_table_combobox = ttk.Combobox(left_bottom_frame, width=10)
    proj_table_combobox["values"] = projection_types
    proj_table_combobox.set("proj_table filter")
    # bind selection event to run on select
    proj_table_combobox.bind("<<ComboboxSelected>>",
                             on_select_proj_table_or_unit)
    proj_table_combobox.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

    # list of units
    units = ["all"]
    units.extend(sorted(set([b.unit for b in bbox])))

    unit_combobox = ttk.Combobox(left_bottom_frame, width=10)
    unit_combobox["values"] = units
    unit_combobox.set("unit filter")
    # bind selection event to run on select
    unit_combobox.bind("<<ComboboxSelected>>", on_select_proj_table_or_unit)
    unit_combobox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    #############
    # right frame
    bottom_frame_width = root_width - left_frame_width
    bottom_frame = tk.Frame(bottom_frame, width=bottom_frame_width)
    bottom_frame.pack_propagate(False)
    bottom_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    #################
    # right-top frame
    right_top_frame = tk.Frame(bottom_frame)
    right_top_frame.pack(fill=tk.BOTH, expand=True)

    # text for CRS info
    crs_text = tk.Text(right_top_frame, width=20, height=1, wrap=tk.NONE)
    crs_text.insert(tk.END, "Select a CRS from the left pane.")
    crs_text.pack(fill=tk.BOTH, expand=True)

    # horizontal scroll bar for CRS info
    info_hscrollbar = tk.Scrollbar(right_top_frame, orient=tk.HORIZONTAL)
    info_hscrollbar.config(command=crs_text.xview)
    info_hscrollbar.pack(side=tk.BOTTOM, fill=tk.BOTH)
    crs_text.config(xscrollcommand=info_hscrollbar.set)

    ####################
    # right-bottom frame
    right_bottom_frame = tk.Frame(bottom_frame)
    right_bottom_frame.pack(fill=tk.BOTH)

    # buttons
    select_button = tk.Button(right_bottom_frame, text="Select", command=select)
    select_button.pack(side=tk.LEFT, expand=True)
    cancel_button = tk.Button(right_bottom_frame, text="Cancel",
                              command=root.destroy)
    cancel_button.pack(side=tk.LEFT, expand=True)

    #########
    # run GUI
    root.mainloop()

    return [find_bbox(crs) for crs in sel_crs]
