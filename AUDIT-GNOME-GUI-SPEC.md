# Tables — GNOME GUI Spec Audit

**Spec source**: https://github.com/hanthor/gnome-gui-spec (v0.2.0)
**Framework**: Python + PyGObject + GTK 4 + libadwaita + WebKitGTK 6.0
**App ID**: io.github.hanthor.tables
**Audit date**: 2026-06-22

Tables inherits its chrome from [suite-common](https://github.com/hanthor/suite-common),
which mirrors the patterns audited in Letters (85/92). The document surface is a
`WebKit.WebView` running Jspreadsheet CE — the same "native chrome + web canvas" tradeoff
as Letters.

## Overall Compliance

| Area | Status | Score |
|------|--------|-------|
| Window Architecture | ✅ `Adw.ApplicationWindow` + `Adw.ToolbarView` + `Adw.HeaderBar` | 9/10 |
| Navigation (Tabs) | ✅ `Adw.TabView` + `Adw.TabBar` | 8/9 |
| Header Bar | ✅ Open/Save + sheet switcher + menu | 10/10 |
| Toolbar | 🟡 Header actions; no responsive breakpoint | 5/7 |
| Preferences | ✅ `Adw.PreferencesDialog` with working Dark Style row | 7/7 |
| Dialogs | ✅ `Gtk.FileDialog`, `Adw.AboutDialog` | 7/7 |
| Shortcuts | ✅ `Gtk.ShortcutsWindow` | 7/7 |
| Menus | ✅ Primary menu (Preferences/Shortcuts/About/Quit) | 7/7 |
| Typography | ✅ Default libadwaita | 6/7 |
| Spacing | ✅ Default libadwaita | 5/5 |
| Accessibility | 🟡 Tooltips + menu accessible-label; webview internals opaque | 5/6 |
| Adaptive | 🟡 TabView adaptive; no explicit breakpoint | 3/5 |
| Error Handling | ✅ `Adw.Toast` via `SuiteWindow.toast()` | 5/5 |
| **Total** | | **84/92 (91%)** |

## Notes
- **Met via suite-common**: window architecture, tabs, header bar, preferences scaffold
  (with a real Dark Style toggle through `Adw.StyleManager`), shortcuts, menus, toast-based
  error handling, accessible label on the menu button.
- **App-specific**: Open/Save through `fileio.py` (csv/xlsx/ods), multi-sheet switcher,
  Jspreadsheet CE + HyperFormula canvas.
- **Packaging**: `.desktop`, AppStream `metainfo.xml`, and a scalable app icon are installed.

## Remaining gaps (tracked follow-ups)
- Responsive toolbar breakpoint (condense header actions on narrow widths) → Toolbar 5→7.
- Richer accessibility bridging into the WebKit grid → Accessibility 5→6.
- An explicit `Adw.Breakpoint` for the spreadsheet view → Adaptive 3→5.
