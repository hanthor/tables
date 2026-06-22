// window.rs — Tables: shared chrome + native cell grid.
use gtk4 as gtk;
use gtk::prelude::*;

const ROWS: usize = 100;
const COLS: usize = 26;

pub struct TablesWindow {
    window: gtk::ApplicationWindow,
}

impl TablesWindow {
    pub fn new(app: &gtk::Application) -> Self {
        let win = gtk::ApplicationWindow::builder().application(app).build();
        win.set_title(Some("Tables"));
        win.set_default_size(900, 600);

        let header = suite_common::make_header_bar();
        let toolbar = suite_common::make_toolbar();
        let formula = gtk::Entry::new();
        formula.set_placeholder_text(Some("Formula…"));

        let model = gtk::gio::ListStore::new(gtk::glib::Type::OBJECT);
        for _ in 0..ROWS { model.append(&gtk::glib::Object::new()); }

        let factory = gtk::SignalListItemFactory::new();
        factory.connect_setup(|_factory, item| {
            let row_box = gtk::Box::new(gtk::Orientation::Horizontal, 0);
            let h = gtk::Label::new(None); h.set_width_chars(4); h.add_css_class("dim-label");
            row_box.append(&h);
            for _ in 0..COLS {
                let e = gtk::Entry::new(); e.set_has_frame(false); e.set_width_chars(10); e.set_hexpand(true);
                row_box.append(&e);
            }
            if let Some(li) = item.downcast_ref::<gtk::ListItem>() { li.set_child(Some(&row_box)); }
        });
        factory.connect_bind(|_factory, item| {
            if let Some(li) = item.downcast_ref::<gtk::ListItem>() {
                let r = li.position() as usize;
                if let Some(c) = li.child() { if let Ok(b) = c.downcast::<gtk::Box>() {
                    if let Some(h) = b.first_child() { if let Ok(l) = h.downcast::<gtk::Label>() { l.set_label(&format!("{}", r + 1)); } }
                    let mut w = b.first_child().and_then(|n| n.next_sibling());
                    let mut col = 0;
                    while let Some(e) = w {
                        if col < COLS { if let Ok(entry) = e.downcast::<gtk::Entry>() {
                            if r == 0 { entry.set_text(&(b'A' + col as u8).to_string()); } else { entry.set_text(""); }
                        }}
                        w = e.next_sibling(); col += 1;
                    }
                }}
            }
        });
        let grid = gtk::ListView::new(Some(gtk::SingleSelection::new(Some(model))), Some(factory));
        let scroll = gtk::ScrolledWindow::new(); scroll.set_child(Some(&grid)); scroll.set_vexpand(true);

        let main = gtk::Box::new(gtk::Orientation::Vertical, 2);
        main.append(&toolbar); main.append(&formula); main.append(&scroll);

        let container = gtk::Box::new(gtk::Orientation::Vertical, 0);
        container.append(&header); container.append(&main);
        win.set_child(Some(&container));
        Self { window: win }
    }
    pub fn present(&self) { self.window.present(); }
}
