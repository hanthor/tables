# window.py — Tables main window.
# SPDX-License-Identifier: GPL-3.0-or-later

import os

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw, GLib  # noqa: E402
from suite_common.window import SuiteWindow  # noqa: E402
from suite_common.webview import SuiteWebView, build_document  # noqa: E402
from . import fileio  # noqa: E402

VENDOR_ASSETS = [
    ('css', 'jsuites.css'),
    ('css', 'jspreadsheet.css'),
    ('js', 'jsuites.js'),
    ('js', 'jspreadsheet.js'),
    ('js', 'hyperformula.full.min.js'),
]


class TablesWindow(SuiteWindow):
    def __init__(self, **kwargs):
        super().__init__(app_name='Tables', **kwargs)
        self._moduledir = os.path.dirname(__file__)
        self._save_path = None
        self._sheet_name = 'Sheet 1'
        self._dirty = False

        self._selftest = os.environ.get('TABLES_SELFTEST')
        self._multitest = os.environ.get('TABLES_MULTITEST')
        print('[tables] selftest =', self._selftest, flush=True)

        self.webview = SuiteWebView(on_message=self._on_message)
        page = self.tab_view.append(self.webview)
        page.set_title('Sheet 1')

        self._add_header_buttons()
        self.webview.load_app(self._build_html())

    # ----- UI ---------------------------------------------------------------

    def _add_header_buttons(self):
        open_btn = Gtk.Button(label='Open')
        open_btn.connect('clicked', lambda *_: self.open_file())
        self.header_bar.pack_start(open_btn)

        save_btn = Gtk.Button(icon_name='document-save-symbolic')
        save_btn.set_tooltip_text('Save')
        save_btn.connect('clicked', lambda *_: self.save_file())
        self.header_bar.pack_start(save_btn)

    def _build_html(self):
        vendor_dir = os.path.join(self._moduledir, 'vendor')
        with open(os.path.join(self._moduledir, 'engine.js'), encoding='utf-8') as fh:
            engine = fh.read()
        body = '<div id="grid" style="height:100vh;width:100%"></div>'
        head_extra = f'<script>{engine}</script>'
        return build_document(vendor_dir, VENDOR_ASSETS, body, head_extra)

    # ----- bridge -----------------------------------------------------------

    def _on_message(self, payload):
        kind = payload.get('type')
        if kind == 'ready':
            print('[tables] engine ready:', payload.get('engine'), flush=True)
            if self._selftest:
                self._run_selftest()
            if self._multitest:
                self._run_multitest()
        elif kind == 'changed':
            self._dirty = True
        elif kind == 'data':
            sheets = payload.get('sheets') or []
            print('[tables] received sheets:', [s.get('name') for s in sheets], flush=True)
            self._save_current(sheets)
            if self._multitest:
                self._verify_multitest()

    # ----- file I/O ---------------------------------------------------------

    def open_file(self):
        dialog = Gtk.FileDialog(title='Open Spreadsheet')
        flt = Gtk.FileFilter()
        flt.set_name('Spreadsheets')
        for pat in ('*.csv', '*.xlsx', '*.ods'):
            flt.add_pattern(pat)
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(flt)
        dialog.set_filters(filters)
        dialog.open(self, None, self._on_open_done)

    def _on_open_done(self, dialog, result):
        try:
            gfile = dialog.open_finish(result)
        except GLib.Error:
            return
        self._load_path(gfile.get_path())

    def _load_path(self, path):
        try:
            sheets = fileio.read_spreadsheet(path)
        except Exception as exc:  # noqa: BLE001
            self._toast(f'Could not open: {exc}')
            return
        payload = []
        for name, rows in sheets:
            width = max((len(r) for r in rows), default=1)
            rect = [list(r) + [''] * (width - len(r)) for r in rows]
            payload.append({'name': name or 'Sheet', 'data': rect})
        self._save_path = path
        self.webview.send('load', payload)
        self._toast(f'Opened {os.path.basename(path)}')

    def save_file(self):
        if self._save_path:
            self.webview.send('getData', None)
            return
        dialog = Gtk.FileDialog(title='Save Spreadsheet')
        dialog.set_initial_name('Untitled.csv')
        dialog.save(self, None, self._on_save_done)

    def _on_save_done(self, dialog, result):
        try:
            gfile = dialog.save_finish(result)
        except GLib.Error:
            return
        self._save_path = gfile.get_path()
        self.webview.send('getData', None)

    def _save_current(self, sheets):
        if not self._save_path:
            return
        out = [(s.get('name') or 'Sheet', self._trim(s.get('data') or [])) for s in sheets]
        if not out:
            out = [('Sheet 1', [])]
        try:
            fileio.write_spreadsheet(self._save_path, out)
        except Exception as exc:  # noqa: BLE001
            self._toast(f'Could not save: {exc}')
            return
        self._dirty = False
        self._toast(f'Saved {os.path.basename(self._save_path)}')

    @staticmethod
    def _trim(data):
        grid = [['' if c is None else str(c) for c in row] for row in data]
        max_col = 0
        for row in grid:
            for i in range(len(row) - 1, -1, -1):
                if row[i] != '':
                    max_col = max(max_col, i + 1)
                    break
        grid = [row[:max_col] for row in grid]
        while grid and all(cell == '' for cell in grid[-1]):
            grid.pop()
        return grid

    # ----- self-test --------------------------------------------------------

    def _run_selftest(self):
        try:
            in_path, _, out_path = self._selftest.partition(':')
            self._load_path(in_path)
            self._save_path = out_path
            GLib.timeout_add(600, self._selftest_pull)
        except Exception as exc:  # noqa: BLE001
            print('[tables] selftest error:', exc, flush=True)

    def _selftest_pull(self):
        print('[tables] selftest requesting data', flush=True)
        self.webview.send('getData', None)
        return False

    def _run_multitest(self):
        try:
            base = self._multitest
            inp = os.path.join(base, 'in.xlsx')
            self._mt_out = os.path.join(base, 'out.xlsx')
            sheets = [('Alpha', [['1', '2'], ['3', '4']]), ('Beta', [['5', '6']])]
            fileio.write_spreadsheet(inp, sheets)   # multi-sheet write
            self._load_path(inp)                    # 2 sheets -> grid (tabs)
            self._save_path = self._mt_out
            GLib.timeout_add(700, lambda: (self.webview.send('getData', None), False)[1])
        except Exception as exc:  # noqa: BLE001
            print('[tables] multitest error:', exc, flush=True)

    def _verify_multitest(self):
        try:
            back = fileio.read_spreadsheet(self._mt_out)
            names = [n for n, _ in back]
            ok = names == ['Alpha', 'Beta']
            print(f'[tables] multitest sheets={names} -> '
                  f'{"PASS" if ok else "FAIL"}', flush=True)
        except Exception as exc:  # noqa: BLE001
            print('[tables] multitest verify error:', exc, flush=True)

    # ----- helpers ----------------------------------------------------------

    def _toast(self, text):
        print('[tables]', text, flush=True)
