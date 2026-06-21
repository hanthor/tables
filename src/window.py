# window.py — Tables main window.
# SPDX-License-Identifier: GPL-3.0-or-later

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Adw  # noqa: E402
from suite_common.window import SuiteWindow  # noqa: E402


class TablesWindow(SuiteWindow):
    def __init__(self, **kwargs):
        super().__init__(app_name='Tables', **kwargs)

        # Tracer-bullet content: a placeholder until the Jspreadsheet CE webview
        # lands (tables #2). Proves the suite-common shell renders.
        status = Adw.StatusPage(
            title='Tables',
            description='Spreadsheet scaffold — libadwaita shell from suite-common.\n'
                        'Next: embed Jspreadsheet CE + HyperFormula (tables #2, #3).',
            icon_name='x-office-spreadsheet-symbolic',
        )
        page = self.tab_view.append(status)
        page.set_title('Sheet 1')
