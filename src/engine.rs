// engine.rs — Spreadsheet engine using Formulizer.
// SPDX-License-Identifier: GPL-3.0-or-later
//
// Formulizer: 400+ Excel functions, Apache Arrow, undo/redo.
// https://github.com/PSU3D0/formualizer

use formualizer::{Workbook, CellValue};
use std::path::Path;

pub struct Spreadsheet {
    wb: Workbook,
    rows: usize,
    cols: usize,
}

impl Spreadsheet {
    pub fn new(rows: usize, cols: usize) -> Result<Self, String> {
        let mut wb = Workbook::new();
        wb.add_sheet("Sheet1", rows as u32, cols as u32)
            .map_err(|e| format!("Create: {}", e))?;
        Ok(Self { wb, rows, cols })
    }

    pub fn set_cell(&mut self, r: usize, c: usize, v: &str) -> Result<(), String> {
        self.wb.set_cell(0, r as u32, c as u32, CellValue::from(v))
            .map_err(|e| format!("Set: {}", e))
    }

    pub fn get_cell(&self, r: usize, c: usize) -> &str {
        ""  // Formulizer reads are async — need to batch
    }

    pub fn to_grid(&self) -> Vec<Vec<String>> {
        vec![vec!["".into(); self.cols]; self.rows]
    }
}

pub fn read_spreadsheet(_path: &Path) -> Result<Spreadsheet, String> {
    Err("Formulizer file I/O: use load_xlsx() from the workbook API".into())
}

pub fn write_spreadsheet(_path: &Path, _ss: &Spreadsheet) -> Result<(), String> {
    Err("Formulizer file I/O: use save_xlsx() from the workbook API".into())
}
