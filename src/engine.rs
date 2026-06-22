// engine.rs — Spreadsheet engine: read/write XLSX/CSV.
// SPDX-License-Identifier: GPL-3.0-or-later
//
// Uses calamine for reading, rust_xlsxwriter for writing.
// Formula engine (IronCalc) will be integrated when API stabilizes.

use calamine::{open_workbook_auto, Reader};
use std::path::Path;

/// Read an XLSX/ODS/CSV file into a 2D grid of strings.
pub fn read_spreadsheet(path: &Path) -> Result<(Vec<Vec<String>>, usize, usize), String> {
    let mut workbook = open_workbook_auto(path)
        .map_err(|e| format!("Failed to open: {}", e))?;

    let sheet_names = workbook.sheet_names().to_vec();
    let name = sheet_names.first().cloned().unwrap_or_default();
    let range = workbook.worksheet_range(&name)
        .map_err(|e| format!("Read error: {}", e))?;

    let rows = range.rows().count();
    let cols = range.rows().next().map(|r| r.len()).unwrap_or(0);
    let mut cells: Vec<Vec<String>> = Vec::with_capacity(rows);

    for row in range.rows() {
        let mut r: Vec<String> = Vec::with_capacity(cols);
        for cell in row {
            r.push(cell.to_string());
        }
        while r.len() < cols { r.push(String::new()); }
        cells.push(r);
    }
    Ok((cells, rows, cols))
}

/// Write a 2D grid to an XLSX file.
pub fn write_spreadsheet(path: &Path, cells: &[Vec<String>]) -> Result<(), String> {
    use rust_xlsxwriter::*;
    let mut workbook = Workbook::new();
    let worksheet = workbook.add_worksheet();

    for (r, row) in cells.iter().enumerate() {
        for (c, cell) in row.iter().enumerate() {
            if !cell.is_empty() {
                worksheet
                    .write_string(r as u32, c as u16, cell)
                    .map_err(|e| format!("Write error: {}", e))?;
            }
        }
    }
    workbook.save(path).map_err(|e| format!("Save error: {}", e))?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_read_write_roundtrip() {
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
