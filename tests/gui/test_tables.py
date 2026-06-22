#!/usr/bin/env python3
# Dogtail GUI test for Tables — drives the running Flatpak via AT-SPI.
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Uses AT-SPI actions (doActionNamed) rather than mouse synthesis, so it works
# headlessly on Wayland (no X display). Run on the HOST against a launched app:
#   python3 tests/gui/test_tables.py        (`just guitest` handles launch/teardown)

import sys
import time

import pyatspi  # noqa: E402
from dogtail import tree  # noqa: E402


def pressed(node):
    # GTK4 toggle buttons expose STATE_PRESSED (not STATE_CHECKED) when active.
    return pyatspi.STATE_PRESSED in node.getState().getStates()


def click(node):
    """Activate a node via its AT-SPI action (no X mouse synthesis)."""
    for action in ('click', 'activate', 'press'):
        try:
            node.doActionNamed(action)
            return
        except Exception:
            continue
    raise AssertionError(f'no clickable action on {node}')


def main():
    app = tree.root.application('tables')
    print('found application: tables')

    bold = app.child(name='Bold', roleName='toggle button')
    italic = app.child(name='Italic', roleName='toggle button')
    app.child(name='Underline', roleName='toggle button')
    print('found formatting toggles: Bold, Italic, Underline')

    assert not pressed(bold), 'Bold should start unpressed'
    click(bold)
    time.sleep(0.6)
    assert pressed(bold), 'Bold should be pressed after AT-SPI click'
    print('Bold toggles via AT-SPI: OK')

    click(italic)
    time.sleep(0.4)
    assert pressed(italic), 'Italic should be pressed after AT-SPI click'
    print('Italic toggles via AT-SPI: OK')

    # The primary menu button (Letters idiom) is findable + activatable.
    menu = app.child(name='Main Menu', roleName='toggle button', showingOnly=False)
    click(menu)
    time.sleep(0.4)
    print('primary menu found + activated: OK')

    # The sheet switcher (workbook tabs) is exposed as a combo box.
    app.child(roleName='combo box', showingOnly=False)
    print('sheet switcher (combo box) found: OK')

    # The WebKit grid is bridged to AT-SPI — many descendant cells are present.
    def count(node):
        total = 1
        try:
            for child in node.children:
                total += count(child)
        except Exception:
            pass
        return total

    descendants = count(app)
    assert descendants > 50, f'expected the grid bridged to AT-SPI, got {descendants} nodes'
    print(f'WebKit grid bridged to AT-SPI: {descendants} accessible nodes')

    print('GUITEST: PASS')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f'GUITEST: FAIL — {exc}')
        sys.exit(1)
