/**
 * runAll.jsx - One-click runner for Premiere workflow (FIXED)
 * Steps:
 *  1) Export timeline -> data/<projectSlug>/timeline_export.csv
 *  2) Merge CSV with txt -> data/<projectSlug>/timeline_export_merged.csv
 *  3) Import resources into bins
 *  4) Cut & push clips using merged CSV
 */

// ===== JSON Polyfill =====
if (typeof JSON === 'undefined') {
    var JSON = {};
}
if (typeof JSON.parse !== 'function') {
    JSON.parse = function (txt) {
        return eval('(' + txt + ')');
    };
}

// ===== Utils =====
function log(msg) {
    try { $.writeln('[runAll] ' + msg); } catch (e) {}
}

function joinPath(a, b) {
    if (!a || a === '') return b || '';
    if (!b || b === '') return a || '';
    var s = a.charAt(a.length - 1);
    return (s === '/' || s === '\\') ? a + b : a + '/' + b;
}

function normalizePath(p) {
    if (!p || p === '') return '';
    return ('' + p).replace(/\\/g, '/').replace(/\/+/g, '/');
}

function fileExists(p) {
    try { return (new File(p)).exists; } catch (e) { return false; }
}

function folderExists(p) {
    try { return (new Folder(p)).exists; } catch (e) { return false; }
}

function ensureFolder(p) {
    try {
        var f = new Folder(p);
        if (!f.exists) return f.create();
        return true;
    } catch (e) {
        return false;
    }
}

function writeTextFile(path, content) {
    try {
        var f = new File(path);
        f.encoding = "UTF-8";
        if (!f.open("w")) return false;
        f.write(content);
        f.close();
        return true;
    } catch (e) {
        alert("Lỗi ghi file: " + e.message);
        return false;
    }
}

function readLines(p, enc) {
    enc = enc || 'UTF-8';
    var f = new File(p);
    f.encoding = enc;
    if (!f.exists) return [];
    if (!f.open('r')) return [];
    var arr = [];
    while (!f.eof) arr.push(f.readln());
    f.close();
    return arr;
}

// parse text file with key=value format
function parsePathTxt(path) {
    try {
        var lines = readLines(path);
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
    } catch (e) {
        alert("Lỗi đọc file text: " + e.message);
        return {};
    }
}

// serialize object to key=value format
function serializePathTxt(cfg) {
    var lines = [];
    for (var key in cfg) {
        if (cfg.hasOwnProperty(key)) {
            lines.push(key + "=" + cfg[key]);
        }
    }
    return lines.join("\n");
}

// ===============================
// PATH RESOLVE (FIXED - NEVER USE _internal/data)
// ===============================

function getScriptFilePath() {
    try {
        return normalizePath(new File($.fileName).fsName);
    } catch (e) {
        return '';
    }
}

// ✅ APP_ROOT = dist/autotool (NOT _internal)
function getAppRootDirFromScript() {
    try {
        var full = getScriptFilePath(); // .../_internal/core/premierCore/runAll.jsx (build)
        if (!full) return null;
        var low = full.toLowerCase();

        var idxInternal = low.indexOf('/_internal/');
        if (idxInternal !== -1) {
            // .../autotool/_internal/... => app root = .../autotool
            var appRootPath = full.substring(0, idxInternal);
            return new Folder(appRootPath);
        }

        // source mode: .../core/premierCore/runAll.jsx => project root = before /core/
        var idxCore = low.indexOf('/core/premiercore/');
        if (idxCore !== -1) {
            var rootPath = full.substring(0, idxCore);
            return new Folder(rootPath);
        }

        // fallback: 3 levels up
        var f = new File($.fileName);
        var premierCoreDir = f.parent;
        var coreDir = premierCoreDir.parent;
        var root = coreDir.parent;
        return root || null;
    } catch (e) {
        return null;
    }
}

function findPathTxt() {
    var possible = [];

    // 1) ưu tiên theo APP_ROOT/data/path.txt
    var appRoot = getAppRootDirFromScript();
    if (appRoot) {
        possible.push(normalizePath(joinPath(appRoot.fsName, 'data/path.txt')));           // ✅ chuẩn
        possible.push(normalizePath(joinPath(appRoot.fsName, 'dist/autotool/data/path.txt'))); // compat
        possible.push(normalizePath(joinPath(appRoot.fsName, '_internal/data/path.txt')));     // compat cũ
    }

    // 2) common paths (giữ để cứu hộ)
    var common = [
        'C:/toolcu/data/path.txt',
        'D:/toolcu/data/path.txt',
        Folder.desktop.fsName + '/toolcu/data/path.txt',
        Folder.desktop.fsName + '/toolcu/autotool/data/path.txt',
        Folder.desktop.fsName + '/autotool/data/path.txt',
        Folder.myDocuments.fsName + '/toolcu/data/path.txt'
    ];
    for (var i = 0; i < common.length; i++) possible.push(normalizePath(common[i]));

    log('Searching for path.txt in ' + possible.length + ' locations...');
    for (var j = 0; j < possible.length; j++) {
        var p = possible[j];
        log('  Checking: ' + p);
        if (fileExists(p)) {
            log('Found path.txt at: ' + p);
            return p;
        }
    }
    return null;
}

function initializePaths() {
    var out = { ROOT_DIR: '', DATA_DIR: '', JSX_DIR: '', PATH_TXT: '' };

    // Resolve APP_ROOT first
    var appRoot = getAppRootDirFromScript();
    if (appRoot) out.ROOT_DIR = normalizePath(appRoot.fsName);

    // Default DATA_DIR = APP_ROOT/data (NEVER _internal/data)
    if (out.ROOT_DIR) out.DATA_DIR = normalizePath(joinPath(out.ROOT_DIR, 'data'));

    // Default JSX_DIR = APP_ROOT/_internal/core/premierCore if exists, else APP_ROOT/core/premierCore
    if (out.ROOT_DIR) {
        var internalJSX = normalizePath(joinPath(out.ROOT_DIR, '_internal/core/premierCore'));
        var normalJSX   = normalizePath(joinPath(out.ROOT_DIR, 'core/premierCore'));
        out.JSX_DIR = folderExists(internalJSX) ? internalJSX : normalJSX;
    }

    // Find and read path.txt (if any)
    var ptxt = findPathTxt();
    if (ptxt) {
        out.PATH_TXT = normalizePath(ptxt);
        var cfg = parsePathTxt(out.PATH_TXT);

        // BUT: chỉ dùng cfg nếu nó hợp lý, và không cho phép data_dir trỏ vào _internal/data
        if (cfg) {
            if (cfg.root_dir) out.ROOT_DIR = normalizePath(cfg.root_dir);

            if (cfg.data_dir) {
                var dd = normalizePath(cfg.data_dir);
                if (dd.toLowerCase().indexOf('/_internal/') === -1) {
                    out.DATA_DIR = dd;
                } else {
                    log('Ignore bad data_dir (_internal): ' + dd);
                }
            }

            if (cfg.jsx_dir) out.JSX_DIR = normalizePath(cfg.jsx_dir);
        }
    }

    // Final ensure
    if (!out.ROOT_DIR) {
        // last fallback: infer from script even if weird
        if (appRoot) out.ROOT_DIR = normalizePath(appRoot.fsName);
    }
    if (!out.DATA_DIR && out.ROOT_DIR) out.DATA_DIR = normalizePath(joinPath(out.ROOT_DIR, 'data'));
    if (!out.JSX_DIR && out.ROOT_DIR) out.JSX_DIR = normalizePath(joinPath(out.ROOT_DIR, '_internal/core/premierCore'));

    ensureFolder(out.DATA_DIR);

    // Ensure PATH_TXT location = DATA_DIR/path.txt
    out.PATH_TXT = normalizePath(joinPath(out.DATA_DIR, 'path.txt'));

    log('Resolved ROOT_DIR: ' + out.ROOT_DIR);
    log('Resolved DATA_DIR: ' + out.DATA_DIR);
    log('Resolved JSX_DIR : ' + out.JSX_DIR);
    log('Resolved PATH_TXT: ' + out.PATH_TXT);

    return out;
}

var _PATHS = initializePaths();
var ROOT_DIR = _PATHS.ROOT_DIR;
var DATA_DIR = _PATHS.DATA_DIR;
var JSX_DIR  = _PATHS.JSX_DIR;
var PATH_TXT = _PATHS.PATH_TXT;

// ===== Read config =====
function readPathConfig() {
    if (!fileExists(PATH_TXT)) {
        log('path.txt not found: ' + PATH_TXT);
        return null;
    }
    return parsePathTxt(PATH_TXT);
}

// ===== Step 1: getTimeline export =====
function runGetTimelineExport(cfg, projectSlug) {
    // update data_folder trong path.txt (ALWAYS write to DATA_DIR/path.txt)
    if (cfg && typeof cfg === 'object') {
        cfg['data_folder'] = normalizePath(joinPath(DATA_DIR, projectSlug));
        cfg['data_dir']    = normalizePath(DATA_DIR);
        cfg['jsx_dir']     = normalizePath(JSX_DIR);
        cfg['root_dir']    = normalizePath(ROOT_DIR);

        // ensure folder exists
        ensureFolder(cfg['data_folder']);

        writeTextFile(PATH_TXT, serializePathTxt(cfg));
        log('Updated path.txt: ' + PATH_TXT);
    }

    // ✅ HARD OVERRIDE for other JSX scripts (so they never use _internal/data)
    RUNALL_DATA_DIR    = normalizePath(DATA_DIR);
    RUNALL_DATA_FOLDER = cfg && cfg['data_folder'] ? normalizePath(cfg['data_folder']) : normalizePath(joinPath(DATA_DIR, projectSlug));
    RUNALL_PATH_TXT    = normalizePath(PATH_TXT);

    var script = normalizePath(joinPath(JSX_DIR, 'getTimeline.jsx'));
    var file = new File(script);
    if (!file.exists) {
        log('getTimeline.jsx not found: ' + script);
        return false;
    }
    try {
        $.writeln('[runAll] Running getTimeline.jsx...');
        $.evalFile(file);
        return true;
    } catch (e) {
        log('Error getTimeline.jsx: ' + e);
        return false;
    }
}

// ===== Step 2: Merge CSV with TXT (using helper.jsx) =====
function mergeCsvWithTxt(cfg, projectSlug) {
    try {
        var helperPath = normalizePath(joinPath(JSX_DIR, 'helper.jsx'));
        var file = new File(helperPath);
        if (!file.exists) {
            $.writeln('[runAll] Warning: helper.jsx not found at ' + helperPath);
            return '';
        }

        // ✅ HARD OVERRIDE for helper.jsx
        RUNALL_DATA_DIR    = normalizePath(DATA_DIR);
        RUNALL_DATA_FOLDER = cfg && cfg['data_folder'] ? normalizePath(cfg['data_folder']) : normalizePath(joinPath(DATA_DIR, projectSlug));
        RUNALL_PATH_TXT    = normalizePath(PATH_TXT);

        $.writeln('[runAll] Loading helper.jsx...');
        $.evalFile(file);

        // find merged csv in most common outputs
        var candidates = [];
        if (cfg && cfg.data_folder) candidates.push(normalizePath(joinPath(cfg.data_folder, 'timeline_export_merged.csv')));
        candidates.push(normalizePath(joinPath(joinPath(DATA_DIR, projectSlug), 'timeline_export_merged.csv')));
        candidates.push(normalizePath(joinPath(DATA_DIR, 'timeline_export_merged.csv')));

        // if helper sets globals
        if (typeof MERGED_CSV_PATH !== 'undefined' && MERGED_CSV_PATH) candidates.unshift(normalizePath(MERGED_CSV_PATH));
        if (typeof RUNALL_MERGED_CSV_PATH !== 'undefined' && RUNALL_MERGED_CSV_PATH) candidates.unshift(normalizePath(RUNALL_MERGED_CSV_PATH));

        for (var i = 0; i < candidates.length; i++) {
            if (fileExists(candidates[i])) return candidates[i];
        }
        return '';
    } catch (e) {
        $.writeln('[runAll] Error in mergeCsvWithTxt: ' + e);
        return '';
    }
}

// ===== Step 3: Import resources =====
function runImportResources(resourceDir) {
    var script = normalizePath(joinPath(JSX_DIR, 'importResource.jsx'));
    var file = new File(script);
    if (!file.exists) {
        log('importResource.jsx not found: ' + script);
        return 0;
    }
    try {
        // ✅ Override for importResource.jsx
        RUNALL_RESOURCE_DIR = normalizePath(resourceDir);
        RUNALL_DATA_DIR     = normalizePath(DATA_DIR);
        RUNALL_PATH_TXT     = normalizePath(PATH_TXT);

        $.writeln('[runAll] Running importResource.jsx...');
        $.evalFile(file);
        var count = (typeof IMPORTED_FILE_COUNT !== 'undefined') ? IMPORTED_FILE_COUNT : 0;
        return count;
    } catch (e) {
        log('Error importResource.jsx: ' + e);
        return 0;
    }
}

// ===== Orchestrate =====
function runAll() {
    var cfg = readPathConfig();
    if (!cfg) {
        alert('Không tìm thấy path.txt tại: ' + PATH_TXT);
        return;
    }

    var projectPath = normalizePath(cfg['project_path'] || '');
    if (!projectPath) {
        alert('Thiếu project_path trong path.txt');
        return;
    }

    // parse project dir + slug robust
    var lastSlash = projectPath.lastIndexOf('/');
    var parentPath = (lastSlash >= 0) ? projectPath.substring(0, lastSlash) : '';
    var projectFile = (lastSlash >= 0) ? projectPath.substring(lastSlash + 1) : projectPath;
    var projectName = projectFile.replace(/\.prproj$/i, '');

    // ✅ projectSlug priority
    var projectSlug =
        ((typeof RUNALL_PROJECT_NAME !== 'undefined' && RUNALL_PROJECT_NAME) ? String(RUNALL_PROJECT_NAME) : '') ||
        (cfg.project_slug ? String(cfg.project_slug) : '') ||
        String(projectName);

    if (!projectSlug) {
        alert('Thiếu projectSlug. Hãy set project_slug trong path.txt');
        return;
    }

    // resource folder next to project: /resource
    var resourceDir = normalizePath(parentPath + '/resource');
    if (!folderExists(resourceDir)) {
        alert('Thư mục resource không tồn tại: ' + resourceDir);
        return;
    }

    // 1) Export timeline
    if (!runGetTimelineExport(cfg, projectSlug)) {
        alert('Xuất timeline thất bại.');
        return;
    }

    // 2) Merge
    var mergedCsv = mergeCsvWithTxt(cfg, projectSlug);
    if (!mergedCsv) {
        alert('Gộp CSV thất bại (không thấy timeline_export_merged.csv).');
        return;
    }
    $.writeln('[runAll] Merged CSV -> ' + mergedCsv);

    // 3) Import resources
    var imported = runImportResources(resourceDir);
    $.writeln('[runAll] Imported files: ' + imported);

    // 4) Cut & Push
    var cpScript = normalizePath(joinPath(JSX_DIR, 'cutAndPush.jsx'));
    if (!fileExists(cpScript)) {
        alert('Không tìm thấy cutAndPush.jsx: ' + cpScript);
        return;
    }
    try {
        RUNALL_TIMELINE_CSV_PATH = normalizePath(mergedCsv);
        RUNALL_DATA_DIR          = normalizePath(DATA_DIR);
        RUNALL_DATA_FOLDER       = cfg && cfg['data_folder'] ? normalizePath(cfg['data_folder']) : normalizePath(joinPath(DATA_DIR, projectSlug));
        RUNALL_PATH_TXT          = normalizePath(PATH_TXT);

        $.writeln('[runAll] Running cutAndPush.jsx with override path: ' + RUNALL_TIMELINE_CSV_PATH);
        $.evalFile(new File(cpScript));
    } catch (e) {
        alert('Lỗi chạy cutAndPush.jsx: ' + e);
    }

    // Save project
    try {
        app.project.save();
        $.writeln('[runAll] Project saved.');
    } catch (e) {
        $.writeln('[runAll] Error saving project: ' + e);
    }

    // Close premiere (nếu muốn)
    try {
        app.quit();
        $.writeln('[runAll] Premiere closed.');
    } catch (e) {
        $.writeln('[runAll] Error closing Premiere: ' + e);
    }

    $.writeln('[runAll] All done.');
}

// Execute
runAll();
