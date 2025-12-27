/**
 * helper.jsx
 * ------------------------------------------
 * Merge timeline_export.csv with list_name.txt -> timeline_export_merged.csv
 * FIX:
 *  - NEVER use _internal/data
 *  - Prefer RUNALL_DATA_FOLDER / RUNALL_DATA_DIR / RUNALL_PATH_TXT
 *  - Do NOT run self-test by default
 *  - When loaded by runAll, auto-merge and set MERGED_CSV_PATH / RUNALL_MERGED_CSV_PATH
 */

var JSX_HELPER_ENCODING = 'UTF-8';

// ===== base utils =====
function _norm(p){ if(!p) return ''; return (''+p).replace(/\\/g,'/').replace(/\/+/g,'/'); }
function _joinPath(a, b) {
	if (!a || a === '') return b || '';
	if (!b || b === '') return a || '';
	var s = a.charAt(a.length - 1);
	return (s === '/' || s === '\\') ? (a + b) : (a + '/' + b);
}
function _isAbs(p){ p=_norm(p); return /^[A-Za-z]:\//.test(p); }
function _fileExists(path) { try { return (new File(path)).exists; } catch (e) { return false; } }
function _folderExists(p) { try { return (new Folder(p)).exists; } catch (e) { return false; } }
function _ensureFolder(p) {
	try { var f = new Folder(_norm(p)); if (!f.exists) return f.create(); return true; }
	catch (e) { return false; }
}
function _readTextFile(p) {
	try {
		var f = new File(p);
		if (!f.exists) return '';
		if (!f.open('r')) return '';
		var t = f.read();
		f.close();
		return t;
	} catch (e) { return ''; }
}
function _parsePathTxt(path) {
	try {
		var content = _readTextFile(path);
		var lines = content.split('\n');
		var cfg = {};
		for (var i = 0; i < lines.length; i++) {
			var line = (lines[i] || '').replace(/^\s+|\s+$/g, '');
			if (line === "" || line.indexOf("=") === -1) continue;
			var parts = line.split("=");
			if (parts.length >= 2) {
				var key = parts[0].replace(/^\s+|\s+$/g, '');
				var value = parts.slice(1).join("=").replace(/^\s+|\s+$/g, '');
				cfg[key] = value;
			}
		}
		return cfg;
	} catch (e) { return {}; }
}

// ✅ appRoot = dist/autotool (NOT _internal)
function _getAppRootDirFromScript(){
	try {
		var full = _norm(new File($.fileName).fsName);
		var low = full.toLowerCase();

		var idxInternal = low.indexOf('/_internal/');
		if (idxInternal !== -1) {
			return new Folder(full.substring(0, idxInternal));
		}

		var idxCore = low.indexOf('/core/premiercore/');
		if (idxCore !== -1) {
			return new Folder(full.substring(0, idxCore));
		}

		var f = new File($.fileName);
		var premierCoreDir = f.parent;
		var coreDir = premierCoreDir.parent;
		var root = coreDir.parent;
		return root || null;
	} catch(e){
		return null;
	}
}

// find path.txt
function _findPathTxt(){
	var possible = [];

	// override from runAll
	try {
		if (typeof RUNALL_PATH_TXT !== 'undefined' && RUNALL_PATH_TXT) possible.push(_norm(String(RUNALL_PATH_TXT)));
	} catch(e0){}

	var appRoot = _getAppRootDirFromScript();
	if (appRoot) {
		possible.push(_norm(_joinPath(appRoot.fsName, 'data/path.txt')));               // ✅ chuẩn
		possible.push(_norm(_joinPath(appRoot.fsName, 'dist/autotool/data/path.txt'))); // compat
		possible.push(_norm(_joinPath(appRoot.fsName, '_internal/data/path.txt')));     // compat cũ
	}

	var common = [
		'C:/toolcu/data/path.txt',
		'D:/toolcu/data/path.txt',
		Folder.desktop.fsName + '/toolcu/data/path.txt',
		Folder.desktop.fsName + '/toolcu/autotool/data/path.txt',
		Folder.desktop.fsName + '/autotool/data/path.txt',
		Folder.myDocuments.fsName + '/toolcu/data/path.txt'
	];
	for (var i=0;i<common.length;i++) possible.push(_norm(common[i]));

	for (var j=0;j<possible.length;j++){
		if (_fileExists(possible[j])) {
			$.writeln('[helper.jsx] Found path.txt at: ' + possible[j]);
			return possible[j];
		}
	}
	return null;
}

// ===== read/write lines =====
function _readAllLines(path, encoding) {
	var f = new File(path);
	f.encoding = encoding || JSX_HELPER_ENCODING;
	if (!f.exists) return [];
	if (!f.open('r')) return [];
	var lines = [];
	while (!f.eof) lines.push(f.readln());
	f.close();
	return lines;
}
function _writeAllText(path, content, encoding) {
	var f = new File(path);
	f.encoding = encoding || JSX_HELPER_ENCODING;
	if (!f.open('w')) return false;
	f.write(content);
	f.close();
	return true;
}

// ===== CSV parser =====
function _parseCSVLine(line) {
	var res = [];
	var cur = '';
	var inQ = false;
	for (var i = 0; i < line.length; i++) {
		var ch = line.charAt(i);
		if (inQ) {
			if (ch === '"') {
				if (i + 1 < line.length && line.charAt(i + 1) === '"') { cur += '"'; i++; }
				else { inQ = false; }
			} else { cur += ch; }
		} else {
			if (ch === ',') { res.push(cur); cur = ''; }
			else if (ch === '"') { inQ = true; }
			else { cur += ch; }
		}
	}
	res.push(cur);
	return res;
}
function _escapeCSVField(val) {
	if (val === null || typeof val === 'undefined') return '';
	var s = String(val);
	var needsQuote = /[",\n\r]/.test(s) || /^\s|\s$/.test(s);
	if (needsQuote) s = '"' + s.replace(/"/g, '""') + '"';
	return s;
}
function _csvJoin(fields) {
	var out = [];
	for (var i = 0; i < fields.length; i++) out.push(_escapeCSVField(fields[i]));
	return out.join(',');
}
function _readCSV(path, encoding) {
	var lines = _readAllLines(path, encoding);
	if (!lines.length) return { header: [], rows: [] };
	var header = _parseCSVLine(lines[0]);
	var rows = [];
	for (var i = 1; i < lines.length; i++) {
		var ln = lines[i];
		if (!ln || ln === '') continue;
		var cols = _parseCSVLine(ln);
		var obj = {};
		for (var c = 0; c < header.length; c++) obj[header[c]] = (c < cols.length) ? cols[c] : '';
		rows.push(obj);
	}
	return { header: header, rows: rows };
}
function _writeCSV(path, header, rows, encoding) {
	var parts = [];
	parts.push(_csvJoin(header));
	for (var i = 0; i < rows.length; i++) {
		var r = rows[i];
		var fields = [];
		for (var h = 0; h < header.length; h++) fields.push(r.hasOwnProperty(header[h]) ? r[header[h]] : '');
		parts.push(_csvJoin(fields));
	}
	return _writeAllText(path, parts.join('\n'), encoding);
}

// ===== Public API =====
function mergeCsvWithTxt(csvIn, txtIn, csvOut, encoding) {
	encoding = encoding || JSX_HELPER_ENCODING;
	if (!csvOut) {
		if (csvIn.toLowerCase().match(/\.csv$/)) csvOut = csvIn.substr(0, csvIn.length - 4) + '_merged.csv';
		else csvOut = csvIn + '_merged.csv';
	}
	var texts = _readAllLines(txtIn, encoding);
	var data = _readCSV(csvIn, encoding);
	var header = data.header.slice(0);
	var rows = data.rows.slice(0);

	var hasText = false;
	for (var i = 0; i < header.length; i++) if (header[i] === 'textContent') { hasText = true; break; }
	if (!hasText) header.push('textContent');

	for (var r = 0; r < rows.length; r++) {
		var t = (r < texts.length) ? (texts[r] || '') : '';
		rows[r]['textContent'] = t;
	}
	_writeCSV(csvOut, header, rows, encoding);
	return csvOut;
}

function mergeCsvWithTxtToPlain(txtOut, csvIn, txtIn, includeHeader, joiner, encoding) {
	encoding = encoding || JSX_HELPER_ENCODING;
	includeHeader = includeHeader === true;
	joiner = (typeof joiner === 'string') ? joiner : ' | ';

	var data = _readCSV(csvIn, encoding);
	var rows = data.rows;

	var overrideTexts = [];
	if (txtIn && _fileExists(txtIn)) overrideTexts = _readAllLines(txtIn, encoding);

	var outParts = [];
	if (includeHeader) outParts.push('# index | start-end(seconds) | name | textContent');

	for (var i = 0; i < rows.length; i++) {
		var r = rows[i];
		var idx = (r.hasOwnProperty('indexInTrack') ? r['indexInTrack'] : '');
		var seg = (r.hasOwnProperty('startSeconds') ? r['startSeconds'] : '') + ' - ' + (r.hasOwnProperty('endSeconds') ? r['endSeconds'] : '');
		var name = (r.hasOwnProperty('name') ? r['name'] : '');
		var t = overrideTexts.length ? ((i < overrideTexts.length) ? overrideTexts[i] : '') : (r.hasOwnProperty('textContent') ? (r['textContent'] || '') : '');
		outParts.push([idx, seg, name, t].join(joiner));
	}
	_writeAllText(txtOut, outParts.join('\n'), encoding);
	return txtOut;
}

// ===== FIX: resolve DATA_FOLDER safely (NO _internal/data) =====
function _resolveDataFolder(){
	// 1) override from runAll
	try {
		if (typeof RUNALL_DATA_FOLDER !== 'undefined' && RUNALL_DATA_FOLDER) {
			var df0 = _norm(String(RUNALL_DATA_FOLDER));
			_ensureFolder(df0);
			return df0;
		}
	} catch(e0){}

	// 2) path.txt
	var pathTxt = _findPathTxt();
	var cfg = null;
	if (pathTxt) cfg = _parsePathTxt(pathTxt);

	var dataDir = '';
	try {
		if (typeof RUNALL_DATA_DIR !== 'undefined' && RUNALL_DATA_DIR) dataDir = _norm(String(RUNALL_DATA_DIR));
	} catch(e1){}

	if (!dataDir && cfg && cfg.data_dir) dataDir = _norm(String(cfg.data_dir));

	var dataFolder = '';
	if (cfg && cfg.data_folder) {
		var df = _norm(String(cfg.data_folder));
		dataFolder = _isAbs(df) ? df : (dataDir ? _norm(_joinPath(dataDir, df)) : df);
	} else if (cfg && cfg.project_slug && dataDir) {
		dataFolder = _norm(_joinPath(dataDir, String(cfg.project_slug)));
	}

	// 3) fallback appRoot/data
	if (!dataDir) {
		var appRoot = _getAppRootDirFromScript();
		if (appRoot) dataDir = _norm(appRoot.fsName + '/data');
		else dataDir = _norm(Folder.desktop.fsName + '/toolcu/data');
	}

	if (!dataFolder) dataFolder = dataDir;

	_ensureFolder(dataDir);
	_ensureFolder(dataFolder);
	return dataFolder;
}

// ===== Auto merge when loaded by runAll =====
function runHelperAutoMerge(){
	try {
		var DATA_FOLDER = _resolveDataFolder(); // string
		var csv_in  = (typeof RUNALL_TIMELINE_CSV_IN !== 'undefined' && RUNALL_TIMELINE_CSV_IN)
			? _norm(String(RUNALL_TIMELINE_CSV_IN))
			: _norm(_joinPath(DATA_FOLDER, 'timeline_export.csv'));

		var txt_in  = (typeof RUNALL_LIST_TXT_IN !== 'undefined' && RUNALL_LIST_TXT_IN)
			? _norm(String(RUNALL_LIST_TXT_IN))
			: _norm(_joinPath(DATA_FOLDER, 'list_name.txt'));

		var csv_out = (typeof RUNALL_TIMELINE_CSV_OUT !== 'undefined' && RUNALL_TIMELINE_CSV_OUT)
			? _norm(String(RUNALL_TIMELINE_CSV_OUT))
			: _norm(_joinPath(DATA_FOLDER, 'timeline_export_merged.csv'));

		var plain_out = _norm(_joinPath(DATA_FOLDER, 'timeline_merged.txt'));

		$.writeln('[helper.jsx] DATA_FOLDER = ' + DATA_FOLDER);
		$.writeln('[helper.jsx] csv_in  = ' + csv_in);
		$.writeln('[helper.jsx] txt_in  = ' + txt_in);
		$.writeln('[helper.jsx] csv_out = ' + csv_out);

		if (!_fileExists(csv_in)) {
			$.writeln('[helper.jsx] ERROR: timeline_export.csv not found: ' + csv_in);
			return '';
		}
		if (!_fileExists(txt_in)) {
			$.writeln('[helper.jsx] WARN: list_name.txt not found: ' + txt_in + ' (still merge with empty texts)');
		}

		var out_path = mergeCsvWithTxt(csv_in, txt_in, csv_out, JSX_HELPER_ENCODING);
		mergeCsvWithTxtToPlain(plain_out, csv_in, txt_in, true, ' | ', JSX_HELPER_ENCODING);

		// set globals for runAll
		MERGED_CSV_PATH = out_path;
		RUNALL_MERGED_CSV_PATH = out_path;

		$.writeln('[helper.jsx] Merged CSV saved to: ' + out_path);
		$.writeln('[helper.jsx] Plain text merged saved to: ' + plain_out);
		return out_path;
	} catch(e){
		$.writeln('[helper.jsx] AutoMerge ERROR: ' + e);
		return '';
	}
}

this.mergeCsvWithTxt = mergeCsvWithTxt;
this.mergeCsvWithTxtToPlain = mergeCsvWithTxtToPlain;
this.runHelperAutoMerge = runHelperAutoMerge;

// ===============================
// SELF TEST (OFF by default)
// ===============================
var RUN_SELF_TEST = false; // ✅ đổi từ true -> false
if (RUN_SELF_TEST) {
	runHelperAutoMerge();
} else {
	// ✅ Nếu đang được gọi từ runAll thì auto merge
	var shouldAuto = false;
	try {
		if ((typeof RUNALL_DATA_FOLDER !== 'undefined' && RUNALL_DATA_FOLDER) ||
			(typeof RUNALL_DATA_DIR !== 'undefined' && RUNALL_DATA_DIR) ||
			(typeof RUNALL_PATH_TXT !== 'undefined' && RUNALL_PATH_TXT)) {
			shouldAuto = true;
		}
	} catch(e2){}
	if (shouldAuto) runHelperAutoMerge();
}
