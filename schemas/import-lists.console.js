/*
 * List importer — paste into the browser DevTools console on the target site's
 * Site contents page (https://<tenant>.sharepoint.com/sites/<site>/_layouts/15/viewlsts.aspx).
 *
 * Pick a folder of schema CSVs (this project's schemas/ folder). For each CSV it:
 *   1. creates the list (named after the file) if it does not exist,
 *   2. creates every field from the ListSchema line, keeping the internal Name
 *      (docs/standards/list-schema-standard.md — internal names are permanent),
 *   3. optionally imports the sample rows ("Import entries").
 * Safe to re-run: existing lists/fields are skipped, sample rows are added only to an empty list.
 *
 * Runs as the signed-in user — they need Manage Lists on the site. No library, no build step.
 *
 * Supported sample-row types: Text, Note, Choice, Number, Currency, Boolean, DateTime, URL.
 * Person and Lookup values are not imported (leave those cells blank). Origin: Acies SPOT, 2026.
 * Chrome/Edge: type "allow pasting" in the console first if it blocks the paste.
 */
(() => {
  'use strict';

  const PANEL_ID = 'acies-list-importer';
  const old = document.getElementById(PANEL_ID);
  if (old) old.remove();

  // ---------- site + REST ----------
  const ctx = window._spPageContextInfo;
  if (!ctx || !ctx.webAbsoluteUrl) {
    alert('Run this on a SharePoint page of the target site (Site contents).');
    return;
  }
  const base = ctx.webAbsoluteUrl.replace(/\/$/, '');

  let digest = null;
  let digestExpires = 0;
  const getDigest = async () => {
    if (digest && Date.now() < digestExpires) return digest;
    const r = await fetch(base + '/_api/contextinfo', {
      method: 'POST', credentials: 'same-origin',
      headers: { Accept: 'application/json;odata=verbose' }
    });
    if (!r.ok) throw new Error('contextinfo ' + r.status);
    const j = (await r.json()).d.GetContextWebInformation;
    digest = j.FormDigestValue;
    digestExpires = Date.now() + (j.FormDigestTimeoutSeconds - 120) * 1000;
    return digest;
  };

  const sleep = (ms) => new Promise((res) => setTimeout(res, ms));

  // Retries 429/503 honouring Retry-After (docs/standards/sharepoint-traps.md — throttling).
  const sp = async (path, { method = 'GET', body, headers = {} } = {}) => {
    for (let attempt = 0; ; attempt++) {
      const h = {
        Accept: 'application/json;odata=verbose',
        'Content-Type': 'application/json;odata=verbose',
        ...headers
      };
      if (method !== 'GET') h['X-RequestDigest'] = await getDigest();
      const r = await fetch(base + '/_api/' + path, {
        method, credentials: 'same-origin', headers: h,
        body: body === undefined ? undefined : JSON.stringify(body)
      });
      if ((r.status === 429 || r.status === 503) && attempt < 5) {
        const ra = Number(r.headers.get('Retry-After'));
        await sleep((ra > 0 ? ra : Math.pow(2, attempt)) * 1000);
        continue;
      }
      const text = await r.text();
      if (!r.ok) {
        let msg = text;
        try { msg = JSON.parse(text).error.message.value; } catch (e) { /* keep raw */ }
        const err = new Error(r.status + ' ' + msg);
        err.status = r.status;
        throw err;
      }
      if (!text) return null;
      const j = JSON.parse(text);
      return j.d !== undefined ? j.d : j;
    }
  };

  const listPath = (title) => "web/lists/getbytitle('" + encodeURIComponent(title.replace(/'/g, "''")) + "')";

  // ---------- file parsing ----------
  const stripBom = (s) => (s.charCodeAt(0) === 0xfeff ? s.slice(1) : s);

  // RFC-4180 style: quoted cells, "" escapes, newlines inside quotes.
  const parseCsv = (text) => {
    const rows = [];
    let row = [], cell = '', q = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (q) {
        if (c === '"') {
          if (text[i + 1] === '"') { cell += '"'; i++; } else q = false;
        } else cell += c;
      } else if (c === '"') q = true;
      else if (c === ',') { row.push(cell); cell = ''; }
      else if (c === '\n' || c === '\r') {
        if (c === '\r' && text[i + 1] === '\n') i++;
        row.push(cell); cell = '';
        if (row.length > 1 || row[0] !== '') rows.push(row);
        row = [];
      } else cell += c;
    }
    if (cell !== '' || row.length) { row.push(cell); rows.push(row); }
    return rows;
  };

  const readSchemaFile = async (file) => {
    const text = stripBom(await file.text());
    const nl = text.search(/\r?\n/);
    const first = nl < 0 ? text : text.slice(0, nl);
    if (!first.startsWith('ListSchema=')) throw new Error('line 1 is not ListSchema=…');
    const schema = JSON.parse(first.slice('ListSchema='.length));
    const fields = schema.schemaXmlList.map((xml) => {
      const el = new DOMParser().parseFromString(xml, 'text/xml').documentElement;
      if (el.nodeName === 'parsererror' || el.getElementsByTagName('parsererror').length) {
        throw new Error('unparseable field XML: ' + xml.slice(0, 80));
      }
      const a = (n) => el.getAttribute(n);
      return {
        xml, name: a('Name'), display: a('DisplayName') || a('Name'), type: a('Type'),
        required: a('Required'), indexed: a('Indexed') === 'TRUE',
        skip: a('FromBaseType') === 'TRUE' || a('Type') === 'Computed' || a('ReadOnly') === 'TRUE'
      };
    });
    const rows = nl < 0 ? [] : parseCsv(text.slice(nl).replace(/^\r?\n/, ''));
    // Optional: "baseTemplate": 101 makes a document library; "existingList": "Site Pages" adds the
    // fields to a list SharePoint already provides, and never creates one.
    const meta = { baseTemplate: schema.baseTemplate || 100, existingList: schema.existingList || null };
    return { fields, header: rows[0] || [], rows: rows.slice(1), meta };
  };

  // ---------- import ----------
  const ADD_OPTIONS = 1 | 8 | 16; // default content type + keep internal Name hint + default view

  // Returns the title of the list the fields go on (the file's own name, or the existing list's).
  const ensureList = async (title, meta, log) => {
    const target = meta.existingList || title;
    try {
      await sp(listPath(target) + '?$select=Id');
      log(meta.existingList ? 'existing list "' + target + '", adding fields' : 'exists, will add any missing fields', 'warn');
      return target;
    } catch (e) {
      if (e.status !== 404) throw e;
    }
    if (meta.existingList) throw new Error('the list "' + target + '" does not exist on this site');
    await sp('web/lists', { method: 'POST', body: { __metadata: { type: 'SP.List' }, BaseTemplate: meta.baseTemplate, Title: title } });
    log(meta.baseTemplate === 101 ? 'document library created' : 'list created', 'ok');
    return target;
  };

  const ensureFields = async (title, fields, log) => {
    const have = new Set(
      (await sp(listPath(title) + '/fields?$select=InternalName&$top=1000')).results.map((f) => f.InternalName)
    );
    const titleDef = fields.find((f) => f.name === 'Title');
    if (titleDef && titleDef.required === 'FALSE') {
      try {
        await sp(listPath(title) + "/fields/getbyinternalnameortitle('Title')", {
          method: 'POST', headers: { 'X-HTTP-Method': 'MERGE', 'IF-MATCH': '*' },
          body: { __metadata: { type: 'SP.Field' }, Required: false }
        });
      } catch (e) { log('Title not made optional: ' + e.message, 'warn'); }
    }
    let made = 0, kept = 0;
    for (const f of fields) {
      if (f.skip) continue;
      if (have.has(f.name)) { kept++; continue; }
      const create = (xml) => sp(listPath(title) + '/fields/createfieldasxml', {
        method: 'POST',
        body: { parameters: { __metadata: { type: 'SP.XmlSchemaFieldCreationInformation' }, SchemaXml: xml, Options: ADD_OPTIONS } }
      });
      let created;
      try {
        created = await create(f.xml);
      } catch (e) {
        // A fixed field ID can collide with an existing site column; retry without it.
        created = await create(f.xml.replace(/\sID="\{[0-9a-fA-F-]+\}"/, ''));
        log(f.name + ': created without its fixed ID (' + e.message.slice(0, 80) + ')', 'warn');
      }
      if (created && created.InternalName !== f.name) {
        log('!! ' + f.name + ' was created as internal name "' + created.InternalName + '" — internal name rule broken: delete the column and fix the CSV', 'err');
      } else if (f.indexed && created && created.Indexed === false) {
        try {
          await sp(listPath(title) + "/fields/getbyinternalnameortitle('" + f.name + "')", {
            method: 'POST', headers: { 'X-HTTP-Method': 'MERGE', 'IF-MATCH': '*' },
            body: { __metadata: { type: 'SP.Field' }, Indexed: true }
          });
        } catch (e) { log(f.name + ': could not index (' + e.message.slice(0, 80) + ')', 'warn'); }
      }
      made++;
    }
    log(made + ' fields created, ' + kept + ' already present', 'ok');
  };

  const toValue = (type, raw) => {
    switch (type) {
      case 'Number': case 'Currency': {
        const n = Number(raw);
        if (isNaN(n)) throw new Error('not a number: ' + raw);
        return n;
      }
      case 'Boolean': return /^(1|true|yes)$/i.test(raw);
      case 'URL': return { __metadata: { type: 'SP.FieldUrlValue' }, Url: raw, Description: raw };
      case 'DateTime': {
        const d = new Date(raw);
        if (isNaN(d.getTime())) throw new Error('not a date: ' + raw);
        return d.toISOString();
      }
      default: return raw;
    }
  };

  const importRows = async (title, data, log) => {
    if (!data.rows.length) { log('no sample rows', 'warn'); return; }
    const byHeader = {};
    data.fields.forEach((f) => { if (!f.skip || f.name === 'Title') { byHeader[f.display] = f; byHeader[f.name] = byHeader[f.name] || f; } });
    const cols = data.header.map((h) => byHeader[h]);
    const unknown = data.header.filter((h, i) => h && !cols[i]);
    if (unknown.length) log('ignored columns: ' + unknown.join(', '), 'warn');
    const entity = (await sp(listPath(title) + '?$select=ListItemEntityTypeFullName')).ListItemEntityTypeFullName;
    // Sample rows go only into an empty list: re-running never duplicates them, and a reference column in a sample
    // row (<Target>Id) holds the row number of its target, which is the target's item ID only in a list created
    // fresh by this importer (SharePoint never reuses an ID, even after a delete).
    const any = await sp(listPath(title) + '/items?$select=Id&$top=1');
    if (any.results.length) { log('list already has items: sample rows skipped', 'warn'); return; }
    let added = 0, failed = 0;
    for (let r = 0; r < data.rows.length; r++) {
      const row = data.rows[r];
      try {
        const body = { __metadata: { type: entity } };
        cols.forEach((f, i) => {
          if (f && row[i] !== undefined && row[i] !== '') body[f.name] = toValue(f.type, row[i]);
        });
        await sp(listPath(title) + '/items', { method: 'POST', body });
        added++;
      } catch (e) {
        failed++;
        log('row ' + (r + 1) + ': ' + e.message.slice(0, 160), 'err');
      }
    }
    log(added + ' rows added' + (failed ? ', ' + failed + ' FAILED' : ''), failed ? 'err' : 'ok');
  };

  // ---------- panel ----------
  const h = (tag, style, props, kids) => {
    const el = document.createElement(tag);
    Object.assign(el.style, style || {});
    Object.assign(el, props || {});
    (kids || []).forEach((k) => el.append(k));
    return el;
  };
  const font = 'Segoe UI, system-ui, sans-serif';
  const btnStyle = { padding: '6px 14px', border: '1px solid #8a8886', background: '#fff', cursor: 'pointer', font: '14px ' + font, borderRadius: '2px' };
  const colors = { ok: '#107c10', warn: '#8a5a00', err: '#a4262c', info: '#201f1e' };

  const panel = h('div', {
    position: 'fixed', top: '60px', right: '16px', width: '520px', maxHeight: '85vh', overflow: 'auto',
    zIndex: 2147483000, background: '#fff', color: '#201f1e', border: '1px solid #8a8886',
    boxShadow: '0 6px 24px rgba(0,0,0,.3)', padding: '16px', font: '14px ' + font
  }, { id: PANEL_ID, role: 'dialog', ariaLabel: 'List importer' });

  const closeBtn = h('button', { ...btnStyle, float: 'right' }, { type: 'button', textContent: 'Close', ariaLabel: 'Close importer' });
  closeBtn.addEventListener('click', () => panel.remove());

  const folderInput = h('input', { display: 'none' }, { type: 'file', id: PANEL_ID + '-folder' });
  folderInput.webkitdirectory = true;
  folderInput.multiple = true;
  const pickBtn = h('button', btnStyle, { type: 'button', textContent: 'Choose schema folder…' });
  pickBtn.addEventListener('click', () => folderInput.click());

  const listBox = h('div', { margin: '12px 0', maxHeight: '240px', overflow: 'auto', border: '1px solid #c8c6c4', padding: '6px' });
  const selectAllLabel = h('label', { display: 'none', fontWeight: '600', margin: '0 0 4px' });
  const selectAll = h('input', { marginRight: '6px' }, { type: 'checkbox', checked: true });
  selectAllLabel.append(selectAll, 'Select all');

  const importEntries = h('input', { marginRight: '6px' }, { type: 'checkbox', id: PANEL_ID + '-entries' });
  const entriesLabel = h('label', { display: 'block', margin: '8px 0' }, { htmlFor: PANEL_ID + '-entries' });
  entriesLabel.append(importEntries, 'Import entries (the sample rows in each CSV — illustrative data)');

  const runBtn = h('button', { ...btnStyle, background: '#0f6cbd', color: '#fff', borderColor: '#0f6cbd' },
    { type: 'button', textContent: 'Import into this site', disabled: true });

  const logBox = h('div', {
    marginTop: '12px', maxHeight: '260px', overflow: 'auto', background: '#faf9f8', border: '1px solid #e1dfdd',
    padding: '6px', font: '12px Consolas, monospace', whiteSpace: 'pre-wrap'
  }, { role: 'log', ariaLive: 'polite' });

  panel.append(
    closeBtn,
    h('div', { fontSize: '16px', fontWeight: '600' }, { textContent: 'List importer' }),
    h('div', { margin: '4px 0 12px', wordBreak: 'break-all' }, { textContent: 'Target: ' + base }),
    pickBtn, folderInput, listBox, entriesLabel, runBtn, logBox
  );
  document.body.append(panel);

  const write = (msg, kind, indent) => {
    logBox.append(h('div', { color: colors[kind || 'info'], paddingLeft: indent ? '14px' : '0' }, { textContent: msg }));
    logBox.scrollTop = logBox.scrollHeight;
    console.log('[list import] ' + msg);
  };

  let items = []; // { file, title, box }
  folderInput.addEventListener('change', () => {
    const files = Array.from(folderInput.files)
      .filter((f) => /\.csv$/i.test(f.name) && !/(^|\/)_reference\//.test(f.webkitRelativePath))
      .sort((a, b) => a.name.localeCompare(b.name));
    listBox.textContent = '';
    items = [];
    if (!files.length) { listBox.textContent = 'No CSV files found in that folder.'; runBtn.disabled = true; return; }
    listBox.append(selectAllLabel);
    selectAllLabel.style.display = 'block';
    files.forEach((file, i) => {
      const id = PANEL_ID + '-f' + i;
      const box = h('input', { marginRight: '6px' }, { type: 'checkbox', checked: true, id });
      const lab = h('label', { display: 'block' }, { htmlFor: id });
      lab.append(box, file.name.replace(/\.csv$/i, ''));
      listBox.append(lab);
      items.push({ file, title: file.name.replace(/\.csv$/i, ''), box });
    });
    runBtn.disabled = false;
  });
  selectAll.addEventListener('change', () => items.forEach((it) => { it.box.checked = selectAll.checked; }));

  runBtn.addEventListener('click', async () => {
    const chosen = items.filter((it) => it.box.checked);
    if (!chosen.length) { write('Nothing selected.', 'warn'); return; }
    const withRows = importEntries.checked;
    if (!confirm('Create ' + chosen.length + ' list(s) on\n' + base + (withRows ? '\nand import their sample rows' : '') + '?')) return;
    [runBtn, pickBtn, importEntries, selectAll].forEach((el) => { el.disabled = true; });
    chosen.forEach((it) => { it.box.disabled = true; });
    let okCount = 0, failCount = 0;
    for (const it of chosen) {
      write('▶ ' + it.title);
      const log = (m, k) => write(m, k, true);
      try {
        const data = await readSchemaFile(it.file);
        const target = await ensureList(it.title, data.meta, log);
        await ensureFields(target, data.fields, log);
        if (withRows) {
          if (data.meta.existingList || data.meta.baseTemplate === 101) log('no sample rows for a library or an existing list', 'warn');
          else await importRows(target, data, log);
        }
        okCount++;
      } catch (e) {
        failCount++;
        log('FAILED: ' + e.message, 'err');
      }
    }
    write('Done — ' + okCount + ' list(s) processed, ' + failCount + ' failed.', failCount ? 'err' : 'ok');
    pickBtn.disabled = false;
  });

  folderInput.focus && pickBtn.focus();
})();
