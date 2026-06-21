# fileio.py — spreadsheet import/export adapters (in-process Python libraries).
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Mirrors Letters' pypandoc approach: convert a file <-> the engine's 2D model.
# xlsx via python-calamine (read) / openpyxl (write); ods via odfpy; csv via stdlib.

import csv
import os


def _ext(path):
    return os.path.splitext(path)[1].lower()


# ----- read -----------------------------------------------------------------

def read_spreadsheet(path):
    """Return a list of (sheet_name, rows_2d) tuples."""
    ext = _ext(path)
    if ext == '.csv':
        with open(path, newline='', encoding='utf-8') as fh:
            return [('Sheet 1', [list(r) for r in csv.reader(fh)])]
    if ext == '.xlsx':
        return _read_xlsx(path)
    if ext == '.ods':
        return _read_ods(path)
    raise ValueError(f'Unsupported format: {ext}')


def _read_xlsx(path):
    from python_calamine import CalamineWorkbook
    wb = CalamineWorkbook.from_path(path)
    sheets = []
    for name in wb.sheet_names:
        rows = wb.get_sheet_by_name(name).to_python()
        sheets.append((name, [['' if c is None else c for c in row] for row in rows]))
    return sheets or [('Sheet 1', [[]])]


def _read_ods(path):
    from odf.opendocument import load
    from odf.table import Table, TableRow, TableCell
    from odf.text import P
    doc = load(path)
    sheets = []
    for table in doc.spreadsheet.getElementsByType(Table):
        name = table.getAttribute('name') or 'Sheet'
        rows = []
        for tr in table.getElementsByType(TableRow):
            row = []
            for tc in tr.getElementsByType(TableCell):
                repeat = int(tc.getAttribute('numbercolumnsrepeated') or 1)
                text = ''.join(str(p) for p in tc.getElementsByType(P))
                row.extend([text] * repeat)
            rows.append(row)
        sheets.append((name, rows))
    return sheets or [('Sheet 1', [[]])]


# ----- write ----------------------------------------------------------------

def write_spreadsheet(path, sheets):
    """sheets: list of (sheet_name, rows_2d)."""
    ext = _ext(path)
    if ext == '.csv':
        _, rows = sheets[0]
        with open(path, 'w', newline='', encoding='utf-8') as fh:
            writer = csv.writer(fh, lineterminator='\n')
            writer.writerows(rows)
        return
    if ext == '.xlsx':
        return _write_xlsx(path, sheets)
    if ext == '.ods':
        return _write_ods(path, sheets)
    raise ValueError(f'Unsupported format: {ext}')


def _coerce(value):
    """Turn grid strings into numbers where they cleanly parse (Excel-like)."""
    if value is None or value == '':
        return None
    if isinstance(value, (int, float)):
        return value
    s = str(value)
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        return s


def _write_xlsx(path, sheets):
    from openpyxl import Workbook
    wb = Workbook()
    wb.remove(wb.active)
    for name, rows in sheets:
        ws = wb.create_sheet(title=name[:31] or 'Sheet')
        for row in rows:
            ws.append([_coerce(c) for c in row])
    wb.save(path)


def _write_ods(path, sheets):
    from odf.opendocument import OpenDocumentSpreadsheet
    from odf.table import Table, TableRow, TableCell
    from odf.text import P
    doc = OpenDocumentSpreadsheet()
    for name, rows in sheets:
        table = Table(name=name or 'Sheet')
        for row in rows:
            tr = TableRow()
            for cell in row:
                tc = TableCell()
                tc.addElement(P(text='' if cell is None else str(cell)))
                tr.addElement(tc)
            table.addElement(tr)
        doc.spreadsheet.addElement(table)
    doc.save(path)
