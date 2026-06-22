/* engine.js — Tables spreadsheet engine: Jspreadsheet CE grid + HyperFormula.
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 * Multi-worksheet (tabs) mode. Talks to Python over the `bridge` channel:
 * posts {type:...} up, receives via window.bridgeReceive.
 * Protocol: load/getData carry a list of {name, data} sheets.
 */
(function () {
  'use strict';

  function post(msg) {
    try { window.webkit.messageHandlers.bridge.postMessage(msg); }
    catch (e) { console.log('bridge post failed: ' + e); }
  }

  var instance = null;  // array of worksheet objects (tabs mode)

  function worksheetArray() {
    if (!instance) { return []; }
    return Array.isArray(instance) ? instance : [instance];
  }

  function build(sheets) {
    var el = document.getElementById('grid');
    el.innerHTML = '';
    if (!sheets || !sheets.length) { sheets = [{ name: 'Sheet 1', data: [['', '', '']] }]; }
    var worksheets = sheets.map(function (s) {
      var data = (s.data && s.data.length) ? s.data : [['', '', '']];
      return { data: data, minDimensions: [12, 30], worksheetName: s.name || 'Sheet' };
    });
    instance = jspreadsheet(el, {
      tabs: true,
      parseFormulas: true,
      worksheets: worksheets,
      onchange: function () { post({ type: 'changed' }); }
    });
  }

  function collect() {
    return worksheetArray().map(function (ws, i) {
      var name = (ws.options && ws.options.worksheetName) || ('Sheet ' + (i + 1));
      return { name: name, data: ws.getData() };
    });
  }

  function init() {
    build([{ name: 'Sheet 1', data: [['', '', ''], ['', '', ''], ['', '', '']] }]);

    try {
      var hf = HyperFormula.buildFromArray(
        [[1], [2], ['=SUM(A1:A2)']], { licenseKey: 'gpl-v3' });
      window.__hf = hf;
      console.log('HyperFormula ready: =SUM(A1:A2) = ' + hf.getCellValue({ sheet: 0, row: 2, col: 0 }));
    } catch (e) {
      console.log('HyperFormula init error: ' + e);
    }

    console.log('Jspreadsheet ready');
    post({ type: 'ready', engine: 'jspreadsheet-ce' });
  }

  // Python -> JS
  window.bridgeReceive = function (name, data) {
    if (name === 'load') {
      build(data);
      post({ type: 'changed' });
    } else if (name === 'getData') {
      post({ type: 'data', sheets: collect() });
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
