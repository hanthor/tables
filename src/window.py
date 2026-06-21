# window.py — Tables main window.
# SPDX-License-Identifier: GPL-3.0-or-later

import csv
import io
import os

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw, GLib  # noqa: E402
from suite_common.window import SuiteWindow  # noqa: E402
from suite_common.webview import SuiteWebView, build_document  # noqa: E402

# Inlined into the page in load order. jSuites is a Jspreadsheet CE dependency.
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
        self._save_path = None      # set when a save target is pending
        self._dirty = False

        # Headless self-test hook: TABLES_SELFTEST="in.csv:out.csv" loads in.csv
        # through the engine and writes the round-tripped data to out.csv on ready.
        self._selftest = os.environ.get('TABLES_SELFTEST')
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
        elif kind == 'changed':
            self._dirty = True
        elif kind == 'data':
            print('[tables] received data rows:', len(payload.get('data') or []), flush=True)
            self._write_csv(payload.get('data') or [])

    # ----- file I/O (CSV; xlsx/ods land in later slices) --------------------

    def open_file(self):
        dialog = Gtk.FileDialog(title='Open Spreadsheet')
        flt = Gtk.FileFilter()
        flt.set_name('Spreadsheets (CSV)')
        flt.add_pattern('*.csv')
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(flt)
        dialog.set_filters(filters)
        dialog.open(self, None, self._on_open_done)

    def _on_open_done(self, dialog, result):
        try:
            gfile = dialog.open_finish(result)
        except GLib.Error:
            return
        path = gfile.get_path()
        try:
            with open(path, newline='', encoding='utf-8') as fh:
                rows = list(csv.reader(fh))
        except OSError as exc:
            self._toast(f'Could not open: {exc}')
            return
        # Pad to a rectangle so Jspreadsheet is happy.
        width = max((len(r) for r in rows), default=1)
        rows = [r + [''] * (width - len(r)) for r in rows]
        self._save_path = path
        self.webview.send('load', rows)
        self._toast(f'Opened {os.path.basename(path)}')

    def save_file(self):
        if self._save_path:
            self.webview.send('getData', None)  # triggers _write_csv via 'data'
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

    def _write_csv(self, data):
        if not self._save_path:
            return
        grid = [['' if c is None else str(c) for c in row] for row in data]
        # Jspreadsheet pads to its min dimensions; trim trailing empty cols/rows.
        max_col = 0
        for row in grid:
            for i in range(len(row) - 1, -1, -1):
                if row[i] != '':
                    max_col = max(max_col, i + 1)
                    break
        grid = [row[:max_col] for row in grid]
        while grid and all(cell == '' for cell in grid[-1]):
            grid.pop()

        buf = io.StringIO()
        writer = csv.writer(buf, lineterminator='\n')
        for row in grid:
            writer.writerow(row)
        try:
            with open(self._save_path, 'w', newline='', encoding='utf-8') as fh:
                fh.write(buf.getvalue())
        except OSError as exc:
            self._toast(f'Could not save: {exc}')
            return
        self._dirty = False
        self._toast(f'Saved {os.path.basename(self._save_path)}')

    # ----- self-test --------------------------------------------------------

    def _run_selftest(self):
        try:
            in_path, _, out_path = self._selftest.partition(':')
            with open(in_path, newline='', encoding='utf-8') as fh:
                rows = list(csv.reader(fh))
            print(f'[tables] selftest loaded {len(rows)} rows from {in_path}', flush=True)
            self._save_path = out_path
            self.webview.send('load', rows)
            # Give the grid a tick to ingest, then pull data back out and write it.
            GLib.timeout_add(600, self._selftest_pull)
        except Exception as exc:  # noqa: BLE001
            print('[tables] selftest error:', exc, flush=True)

    def _selftest_pull(self):
        print('[tables] selftest requesting data', flush=True)
        self.webview.send('getData', None)
        return False

    # ----- helpers ----------------------------------------------------------

    def _toast(self, text):
        print('[tables]', text, flush=True)
