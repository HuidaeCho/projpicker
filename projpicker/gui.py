"""
This module implements the GUI of ProjPicker.
"""

import sys
import re
import projpicker as ppik
import tkinter as tk
from tkinter import ttk
import textwrap


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
    prev_sel_crs_ls = []

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

        auth, code = extract_crs_auth_code(crs).split(":")
        b = list(filter(lambda b: b.crs_auth_name==auth and
                                  b.crs_code==code, bbox))[0]
        return b


    def on_select_crs(event):
        nonlocal prev_sel_crs_ls

        w = event.widget
        last_crs_ls = w.curselection()

        if single:
            prev_sel_crs_ls.clear()

        if len(last_crs_ls) > len(prev_sel_crs_ls):
            # selected a new crs
            last_crs_ls = list(set(last_crs_ls) - set(prev_sel_crs_ls))[0]
            prev_sel_crs_ls.append(last_crs_ls)
        elif len(last_crs_ls) < len(prev_sel_crs_ls):
            # deselected an existing crs
            last_crs_ls = list(set(prev_sel_crs_ls) - set(last_crs_ls))[0]
            del prev_sel_crs_ls[prev_sel_crs_ls.index(last_crs_ls)]
            l = len(prev_sel_crs_ls)
            if l > 0:
                last_crs_ls = prev_sel_crs_ls[l-1]
            else:
                last_crs_ls = None
        else:
            last_crs_ls = None

        crs_text.delete("1.0", tk.END)
        if last_crs_ls is not None:
            crs_info = create_crs_info(find_bbox(w.get(last_crs_ls)))
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

        crs_listbox.delete(0, tk.END)
        for b in filt_bbox:
            crs_listbox.insert(tk.END, f"{b.crs_name} "
                                       f"({b.crs_auth_name}:{b.crs_code})")
        prev_sel_crs_ls.clear()


    def select():
        nonlocal sel_crs

        for i in crs_listbox.curselection():
            sel_crs.append(extract_crs_auth_code(crs_listbox.get(i)))
        root.destroy()


    # root window
    root = tk.Tk()
    root.geometry("800x400")
    root.title("ProjPicker GUI")
    root.resizable(False, False)

    ############
    # left frame
    left_frame = tk.Frame(root, width=500)
    left_frame.pack_propagate(False)
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    ################
    # top-left frame
    topleft_frame = tk.Frame(left_frame)
    topleft_frame.pack(fill=tk.BOTH, expand=True)

    # list of CRSs
    crs_listbox = tk.Listbox(topleft_frame,
                             selectmode=tk.SINGLE if single else tk.MULTIPLE)
    for b in bbox:
        crs_listbox.insert(tk.END,
                           f"{b.crs_name} ({b.crs_auth_name}:{b.crs_code})")
    crs_listbox.bind("<<ListboxSelect>>", on_select_crs)
    crs_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # vertical scroll bar for CRS list
    list_vscrollbar = tk.Scrollbar(topleft_frame)
    list_vscrollbar.config(command=crs_listbox.yview)
    list_vscrollbar.pack(side=tk.LEFT, fill=tk.BOTH)
    crs_listbox.config(yscrollcommand=list_vscrollbar.set)

    ################
    # middle-left frame
    middleleft_frame = tk.Frame(left_frame)
    middleleft_frame.pack(fill=tk.BOTH)

    # horizontal scroll bar for CRS list
    list_hscrollbar = tk.Scrollbar(middleleft_frame, orient=tk.HORIZONTAL)
    list_hscrollbar.config(command=crs_listbox.xview)
    list_hscrollbar.pack(side=tk.BOTTOM, fill=tk.BOTH)
    crs_listbox.config(xscrollcommand=list_hscrollbar.set)

    ###################
    # bottom-left frame
    bottomleft_frame = tk.Frame(left_frame)
    bottomleft_frame.pack(fill=tk.X, ipady=3, pady=2, padx=2)

    # list box for projection types
    projection_types = ["all"]
    projection_types.extend(sorted(set([b.proj_table for b in bbox])))

    proj_table_combobox = ttk.Combobox(bottomleft_frame, width=10)
    proj_table_combobox["values"] = projection_types
    proj_table_combobox.set("proj_table filter")
    # bind selection event to run on select
    proj_table_combobox.bind("<<ComboboxSelected>>",
                             on_select_proj_table_or_unit)
    proj_table_combobox.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

    # list of units
    units = ["all"]
    units.extend(sorted(set([b.unit for b in bbox])))

    unit_combobox = ttk.Combobox(bottomleft_frame, width=10)
    unit_combobox["values"] = units
    unit_combobox.set("unit filter")
    # bind selection event to run on select
    unit_combobox.bind("<<ComboboxSelected>>", on_select_proj_table_or_unit)
    unit_combobox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    #############
    # right frame
    right_frame = tk.Frame(root, width=300)
    right_frame.pack_propagate(False)
    right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    #################
    # top-right frame
    topright_frame = tk.Frame(right_frame)
    topright_frame.pack(fill=tk.BOTH, expand=True)

    # text for CRS info
    crs_text = tk.Text(topright_frame, width=20, wrap=tk.NONE)
    crs_text.insert(tk.END, "Select a CRS from the left pane.")
    crs_text.pack(fill=tk.BOTH, expand=True)

    # horizontal scroll bar for CRS info
    info_hscrollbar = tk.Scrollbar(topright_frame, orient=tk.HORIZONTAL)
    info_hscrollbar.config(command=crs_text.xview)
    info_hscrollbar.pack(side=tk.BOTTOM, fill=tk.BOTH)
    crs_text.config(xscrollcommand=info_hscrollbar.set)

    ####################
    # bottom-right frame
    bottomright_frame = tk.Frame(right_frame)
    bottomright_frame.pack(fill=tk.BOTH)

    # buttons
    select_button = tk.Button(bottomright_frame, text="Select", command=select)
    select_button.pack(side=tk.LEFT, expand=True)
    cancel_button = tk.Button(bottomright_frame, text="Cancel",
                              command=root.destroy)
    cancel_button.pack(side=tk.LEFT, expand=True)

    #########
    # run GUI
    root.mainloop()

    return [find_bbox(crs) for crs in sel_crs]
