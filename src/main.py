# main.py — Tables application entry point.
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Adw  # noqa: E402
from suite_common.application import SuiteApplication  # noqa: E402
from .window import TablesWindow  # noqa: E402


class TablesApplication(SuiteApplication):
    def __init__(self, version):
        super().__init__(application_id='io.github.hanthor.tables',
                         window_class=TablesWindow,
                         app_name='Tables',
                         version=version)


def main(version):
    Adw.init()
    app = TablesApplication(version)
    return app.run(sys.argv)
