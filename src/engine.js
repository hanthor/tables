/* engine.js — Tables spreadsheet engine: Jspreadsheet CE grid + HyperFormula.
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 * Loaded into the suite-common SuiteWebView. Talks to Python over the `bridge`
 * script-message channel: posts {type:...} up, receives via window.bridgeReceive.
 */
(function () {
  'use strict';

  function post(msg) {
    try { window.webkit.messageHandlers.bridge.postMessage(msg); }
    catch (e) { console.log('bridge post failed: ' + e); }
  }

  var sheet = null;

  function currentData() {
    return sheet ? sheet.getData() : [];
  }

  function init() {
    var container = document.getElementById('grid');

    sheet = jspreadsheet(container, {
      data: [['', '', ''], ['', '', ''], ['', '', '']],
      minDimensions: [12, 30],
      parseFormulas: true,         // live formula recalc (=SUM, etc.)
      columnSorting: true,
      onchange: function () { post({ type: 'changed' }); },
      onload: function () { post({ type: 'changed' }); }
    });
    window.__sheet = sheet;

    // HyperFormula (GPL): Excel-compatible engine, used for verification now and
    // as the export-time evaluator. Proves the dependency loads + computes.
    try {
      var hf = HyperFormula.buildFromArray(
        [[1], [2], ['=SUM(A1:A2)']], { licenseKey: 'gpl-v3' });
      var v = hf.getCellValue({ sheet: 0, row: 2, col: 0 });
      window.__hf = hf;
      console.log('HyperFormula ready: =SUM(A1:A2) = ' + v);
    } catch (e) {
      console.log('HyperFormula init error: ' + e);
    }

    console.log('Jspreadsheet ready');
    post({ type: 'ready', engine: 'jspreadsheet-ce' });
  }

  // Python -> JS
  window.bridgeReceive = function (name, data) {
    if (name === 'load') {
      if (sheet && data && data.length) { sheet.setData(data); }
      post({ type: 'changed' });
    } else if (name === 'getData') {
      post({ type: 'data', data: currentData() });
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
