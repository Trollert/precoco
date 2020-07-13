from tkinter import Tk, BooleanVar
from pathlib import Path

error_log = []
root_dir = str((Path(__file__).parent / "..").resolve())
# (Path(__file__).parent / "../data").resolve()

# global flags
flag_found_error = False
flag_is_formatted = False

tk = Tk()
# Bools to define which functions to call
b_split_rowspan = BooleanVar(value=1)
b_set_footnotes = BooleanVar(value=1)
b_fix_numbers = BooleanVar(value=1)
b_rename_pics = BooleanVar(value=1)
b_merge_tables_vertically = BooleanVar(value=1)
b_span_headings = BooleanVar(value=0)
b_set_unordered_lists = BooleanVar(value=1)
b_indent_unordered_list = BooleanVar(value=1)
b_set_headers = BooleanVar(value=1)
b_sup_elements = BooleanVar(value=0)
b_remove_empty_rows = BooleanVar(value=1)
b_fix_tsd_separators = BooleanVar(value=1)
b_break_fonds_table = BooleanVar(value=1)
b_remove_false_text_breaks = BooleanVar(value=1)
# bool to identify fonds reports
b_fonds_report = BooleanVar(value=0)
