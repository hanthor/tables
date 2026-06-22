#!/usr/bin/env python3
# Dogtail GUI test for Tables — drives the running Flatpak via AT-SPI.
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Run on the HOST (not in the flatpak), against an already-launched app:
#   python3 tests/gui/test_tables.py
# `just guitest` handles launch/teardown.

import sys
import time

from dogtail.config import config

config.searchBackoffDuration = 1.0
config.searchCutoffCount = 25
config.actionDelay = 0.4
config.defaultDelay = 0.4

from dogtail import tree  # noqa: E402


def main():
    app = tree.root.application('tables')
    print('found application: tables')

    # The formatting toolbar (Letters idiom) — toggle buttons with a11y names.
    bold = app.child(name='Bold', roleName='toggle button')
    italic = app.child(name='Italic', roleName='toggle button')
    underline = app.child(name='Underline', roleName='toggle button')
    print('found formatting toggles: Bold, Italic, Underline')

    # Drive the UI: click Bold, assert its accessible state flips.
    assert not bold.checked, 'Bold should start unchecked'
    bold.click()
    time.sleep(0.6)
    assert bold.checked, 'Bold should be checked after click'
    print('Bold toggles via AT-SPI: OK')

    italic.click()
    time.sleep(0.4)
    assert italic.checked, 'Italic should be checked after click'
    print('Italic toggles via AT-SPI: OK')

    # Alignment push buttons + header actions are findable by name.
    for name in ('Align Left', 'Align Center', 'Align Right'):
        app.child(name=name, roleName='push button')
    print('found alignment buttons')

    for name in ('Open', 'Save'):
        app.child(name=name, roleName='push button')
    print('found header buttons: Open, Save')

    # The primary menu button is findable (role varies: toggle/push button).
    menu = app.child(name='Main Menu')
    menu.click()
    time.sleep(0.5)
    print('primary menu button found + clicked: OK')

    print('GUITEST: PASS')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f'GUITEST: FAIL — {exc}')
        sys.exit(1)
