// window.rs — Tables: shared chrome + native cell grid.
// SPDX-License-Identifier: GPL-3.0-or-later

use gtk4 as gtk;
use gtk::prelude::*;

const ROWS: usize = 100;
const COLS: usize = 26;

pub struct TablesWindow {
    window: gtk::ApplicationWindow,
}

impl TablesWindow {
    pub fn new(app: &gtk::Application) -> Self {
        let win = gtk::ApplicationWindow::new(app);
        win.set_title(Some("Tables"));
        win.set_default_size(800, 600);

        let header = suite_common::make_header_bar();
        let toolbar = suite_common::make_toolbar();
        let formula_bar = gtk::Entry::new();
        formula_bar.set_placeholder_text(Some("Formula…"));

        // Cell grid placeholder
        let grid = gtk::Label::new(Some("🦀 Tables — Rust native with suite-common"));
        grid.set_vexpand(true);

        let main_box = gtk::Box::new(gtk::Orientation::Vertical, 2);
        main_box.append(&toolbar);
        main_box.append(&formula_bar);
        main_box.append(&grid);

        let container = gtk::Box::new(gtk::Orientation::Vertical, 0);
        container.append(&header);
        container.append(&main_box);
        win.set_child(Some(&container));

        Self { window: win }
    }

    pub fn present(&self) {
        self.window.present();
    }
}
