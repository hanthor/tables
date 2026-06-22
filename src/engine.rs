// engine.rs — Spreadsheet engine using IronCalc exclusively.
// SPDX-License-Identifier: GPL-3.0-or-later

use ironcalc_base::Model;

/// Wrapper around IronCalc Model<'static>.
pub struct Spreadsheet {
    model: Model<'static>,
    path: Option<String>,
}

impl Spreadsheet {
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

    pub fn load(path: &str) -> Result<Self, String> {
        // load_from_xlsx returns Model<'a>. We need Model<'static>.
        // Strategy: load, serialize to bytes, deserialize.
        let tmp_model = ironcalc::import::load_from_xlsx(path, "en_US", "UTC", "en")
            .map_err(|e| format!("Load: {}", e))?;
        let bytes = tmp_model.to_bytes()
            .map_err(|e| format!("Serialize: {}", e))?;
        let model = Model::from_bytes(&bytes, "en", "UTC", "en")
            .map_err(|e| format!("Deserialize: {}", e))?;
        Ok(Self { model, path: Some(path.to_string()) })
    }

    pub fn save(&self, path: &str) -> Result<(), String> {
        ironcalc::export::save_to_xlsx(&self.model, path)
            .map_err(|e| format!("Save: {}", e))?;
        Ok(())
    }

    pub fn get_cell(&self, row: usize, col: usize) -> String {
        self.model
            .get_cell_value_by_index(0, row as i32 + 1, col as i32 + 1)
            .map(|v| v.to_string())
            .unwrap_or_default()
    }

    pub fn set_cell(&mut self, row: usize, col: usize, value: &str) -> Result<(), String> {
        self.model.set_user_input(0, row as i32 + 1, col as i32 + 1, value)
            .map_err(|e| format!("Set cell: {}", e))?;
        Ok(())
    }

    pub fn to_grid(&self) -> Vec<Vec<String>> {
        let cells = self.model.get_all_cells(0).unwrap_or_default();
        let rows = cells.len();
        let cols = cells.first().map(|r| r.len()).unwrap_or(0);
        let mut grid = Vec::with_capacity(rows);
        for r in 0..rows {
            let mut row = Vec::with_capacity(cols);
            for c in 0..cols {
                row.push(
                    cells[r][c].as_ref()
                        .map(|v| v.to_string())
                        .unwrap_or_default()
                );
            }
            grid.push(row);
        }
        grid
    }
}

pub fn read_spreadsheet(path: &std::path::Path) -> Result<(Vec<Vec<String>>, usize, usize), String> {
    let ss = Spreadsheet::load(path.to_str().unwrap())?;
    let grid = ss.to_grid();
    let rows = grid.len();
    let cols = grid.first().map(|r| r.len()).unwrap_or(0);
    Ok((grid, rows, cols))
}

pub fn write_spreadsheet(path: &std::path::Path, cells: &[Vec<String>]) -> Result<(), String> {
    let mut ss = Spreadsheet::new(
        cells.len(),
        cells.first().map(|r| r.len()).unwrap_or(0),
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
    fn test_set_get() {
        let mut ss = Spreadsheet::new(3, 2).unwrap();
        ss.set_cell(0, 0, "Hello").unwrap();
        assert_eq!(ss.get_cell(0, 0), "Hello");
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
        let (back, _, _) = read_spreadsheet(&path).unwrap();
        assert_eq!(back[0][0], "Name");
        assert_eq!(back[1][1], "30");
    }
}
