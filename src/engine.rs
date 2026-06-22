// engine.rs — Spreadsheet engine using IronCalc exclusively.
// SPDX-License-Identifier: GPL-3.0-or-later
//
// Decision 2026-06-22: IronCalc is the spreadsheet engine.
// Uses ironcalc_base crate (the engine) for Model, set_user_input, etc.
// ironcalc crate (umbrella) handles import/export (load_from_xlsx, save_to_xlsx).
//
// API reference: https://docs.rs/ironcalc_base

use ironcalc_base::Model;

/// Wrapper around IronCalc Model with convenience accessors.
pub struct Spreadsheet {
    model: Model,
    path: Option<String>,
}

impl Spreadsheet {
    /// Create a new empty spreadsheet.
    pub fn new(rows: usize, cols: usize) -> Result<Self, String> {
        let mut model = Model::new_empty("untitled", "en", "UTC", "en")
            .map_err(|e| format!("Create: {}", e))?;
        for r in 0..rows {
            for c in 0..cols {
                model.set_user_input(0, r as i32 + 1, c as i32 + 1, "")
                    .map_err(|e| format!("Set: {}", e))?;
            }
        }
        Ok(Self { model, path: None })
    }

    /// Load from an XLSX file.
    pub fn load(path: &str) -> Result<Self, String> {
        let path_owned = path.to_string();
        // IronCalc load_from_xlsx returns Model<'a> with lifetime tied to input.
        // We need a Model<'static> for storage. Strategy: load, save to icalc, reload.
        let model = ironcalc::import::load_from_xlsx(&path_owned, "en_US", "UTC", "en")
            .map_err(|e| format!("Load: {}", e))?;
        Ok(Self { model, path: Some(path.to_string()) })
    }

    /// Save to XLSX.
    pub fn save(&self, path: &str) -> Result<(), String> {
        ironcalc::export::save_to_xlsx(&self.model, path)
            .map_err(|e| format!("Save: {}", e))?;
        Ok(())
    }

    /// Auto-save to the loaded path.
    pub fn auto_save(&self) -> Result<(), String> {
        if let Some(ref p) = self.path {
            self.save(p)
        } else {
            Ok(())
        }
    }

    /// Get cell value at 0-based (row, col).
    pub fn get_cell(&self, row: usize, col: usize) -> String {
        self.model.get_cell(0, row as i32 + 1, col as i32 + 1)
            .and_then(|c| c.read())
            .unwrap_or_else(|_| "".to_string())
    }

    /// Set cell value at 0-based (row, col).
    pub fn set_cell(&mut self, row: usize, col: usize, value: &str) -> Result<(), String> {
        self.model.set_user_input(0, row as i32 + 1, col as i32 + 1, value)
            .map_err(|e| format!("Set cell: {}", e))?;
        Ok(())
    }

    /// Return rows and cols.
    pub fn dimensions(&self) -> (usize, usize) {
        // IronCalc sheets are dynamic — approximate from metadata
        let sheet = self.model.get_sheet(0)
            .ok()
            .flatten()
            .map(|s| (s.rows(), s.columns()))
            .unwrap_or((100, 26));
        (sheet.0 as usize, sheet.1 as usize)
    }

    /// Return cell values as a 2D grid for display.
    pub fn to_grid(&self) -> Vec<Vec<String>> {
        let (rows, cols) = self.dimensions();
        let mut cells = Vec::with_capacity(rows);
        for r in 0..rows {
            let mut row = Vec::with_capacity(cols);
            for c in 0..cols {
                row.push(self.get_cell(r, c));
            }
            cells.push(row);
        }
        cells
    }
}

/// Read XLSX file via IronCalc.
pub fn read_spreadsheet(path: &std::path::Path) -> Result<(Vec<Vec<String>>, usize, usize), String> {
    let ss = Spreadsheet::load(path.to_str().unwrap())?;
    let grid = ss.to_grid();
    let rows = grid.len();
    let cols = grid.first().map(|r| r.len()).unwrap_or(0);
    Ok((grid, rows, cols))
}

/// Write grid to XLSX via IronCalc.
pub fn write_spreadsheet(path: &std::path::Path, cells: &[Vec<String>]) -> Result<(), String> {
    let mut ss = Spreadsheet::new(
        cells.len(),
        cells.first().map(|r| r.len()).unwrap_or(0)
    )?;
    for (r, row) in cells.iter().enumerate() {
        for (c, cell) in row.iter().enumerate() {
            if !cell.is_empty() {
                ss.set_cell(r, c, cell)?;
            }
        }
    }
    ss.save(path.to_str().unwrap())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_new_empty() {
        let ss = Spreadsheet::new(3, 2).unwrap();
        assert_eq!(ss.get_cell(0, 0), "");
    }

    #[test]
    fn test_set_get() {
        let mut ss = Spreadsheet::new(3, 2).unwrap();
        ss.set_cell(0, 0, "Hello").unwrap();
        ss.set_cell(1, 1, "World").unwrap();
        assert_eq!(ss.get_cell(0, 0), "Hello");
        assert_eq!(ss.get_cell(1, 1), "World");
    }

    #[test]
    fn test_roundtrip() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("test.xlsx");
        let data = vec![
            vec!["Name".into(), "Age".into()],
            vec!["Alice".into(), "30".into()],
        ];
        write_spreadsheet(&path, &data).unwrap();
        let (back, rows, cols) = read_spreadsheet(&path).unwrap();
        assert_eq!(rows, 2);
        assert_eq!(cols, 2);
        assert_eq!(back[0][0], "Name");
        assert_eq!(back[1][1], "30");
    }
}
