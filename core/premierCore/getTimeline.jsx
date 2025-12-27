/**
 * getTimeline.jsx
 * ------------------------------------------
 * Export timeline ranges to DATA_FOLDER/timeline_export.json + timeline_export.csv
 * FIX:
 *  - NEVER fall back to _internal/data
 *  - Prefer RUNALL_DATA_FOLDER / RUNALL_DATA_DIR / RUNALL_PATH_TXT
 *  - If script is under .../_internal/core/premierCore, app root = parent of _internal
 */

// ===== Polyfill JSON =====
if (typeof JSON === 'undefined') { var JSON = {}; }
if (typeof JSON.stringify !== 'function') {
	JSON.stringify = (function(){
		function esc(str){
			return ('"' + String(str)
				.replace(/\\/g,'\\\\')
				.replace(/"/g,'\\"')
				.replace(/\r/g,'\\r')
				.replace(/\n/g,'\\n')
				.replace(/\t/g,'\\t')
				.replace(/\f/g,'\\f')
				.replace(/\b/g,'\\b') + '"');
		}
		function isArr(v){ return Object.prototype.toString.call(v)==='[object Array]'; }
		function stringify(v){
			var t = typeof v;
			if (v === null) return 'null';
			if (t === 'number' || t === 'boolean') return ''+v;
			if (t === 'string') return esc(v);
			if (t === 'undefined' || t === 'function') return 'null';
			if (isArr(v)) {
				var outA = [];
				for (var i=0;i<v.length;i++) outA.push(stringify(v[i]));
				return '[' + outA.join(',') + ']';
			}
			var parts = [];
			for (var k in v) if (v.hasOwnProperty(k)) parts.push(esc(k)+ ':' + stringify(v[k]));
			return '{' + parts.join(',') + '}';
		}
		return function(value){ return stringify(value); };
	})();
}
if (typeof JSON.parse !== 'function') {
	JSON.parse = function(txt){ return eval('(' + txt + ')'); };
}

// ===== Helpers for path + I/O =====
function _norm(p){
	if (!p) return '';
	return (''+p).replace(/\\/g,'/').replace(/\/+/g,'/');
}
function _joinPath(a, b) {
	if (!a || a === '') return b || '';
	if (!b || b === '') return a || '';
	var s = a.charAt(a.length - 1);
	return (s === '/' || s === '\\') ? (a + b) : (a + '/' + b);
}
function _isAbs(p){
	p = _norm(p);
	return /^[A-Za-z]:\//.test(p);
}
function _fileExists(p) { try { return (new File(p)).exists; } catch (e) { return false; } }
function _folderExists(p) { try { return (new Folder(p)).exists; } catch (e) { return false; } }
function _ensureFolder(p) {
	try {
		p = _norm(p);
		var f = new Folder(p);
		if (!f.exists) return f.create();
		return true;
	} catch (e) { return false; }
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
	} catch (e) {
		$.writeln("[getTimeline] Lỗi đọc path.txt: " + e.message);
		return {};
	}
}

// ✅ appRoot = dist/autotool (NOT _internal)
function _getAppRootDirFromScript(){
	try {
		var full = _norm(new File($.fileName).fsName);
		var low = full.toLowerCase();

		var idxInternal = low.indexOf('/_internal/');
		if (idxInternal !== -1) {
			var appRootPath = full.substring(0, idxInternal);
			return new Folder(appRootPath);
		}

		var idxCore = low.indexOf('/core/premiercore/');
		if (idxCore !== -1) {
			var rootPath = full.substring(0, idxCore);
			return new Folder(rootPath);
		}

		// fallback 3 levels up
		var f = new File($.fileName);
		var premierCoreDir = f.parent;
		var coreDir = premierCoreDir.parent;
		var root = coreDir.parent;
		return root || null;
	} catch(e){
		return null;
	}
}

// Try to find path.txt in multiple possible locations
function _findPathTxt() {
	var possiblePaths = [];

	// 0) Prefer override from runAll
	try {
		if (typeof RUNALL_PATH_TXT !== 'undefined' && RUNALL_PATH_TXT) {
			var p0 = _norm(String(RUNALL_PATH_TXT));
			possiblePaths.push(p0);
		}
	} catch(e0){}

	// 1) app root derived from script
	try {
		var appRoot = _getAppRootDirFromScript(); // dist/autotool
		if (appRoot) {
			possiblePaths.push(_norm(_joinPath(appRoot.fsName, 'data/path.txt')));                // ✅ chuẩn
			possiblePaths.push(_norm(_joinPath(appRoot.fsName, 'dist/autotool/data/path.txt')));  // compat
			possiblePaths.push(_norm(_joinPath(appRoot.fsName, '_internal/data/path.txt')));      // compat cũ
		}
	} catch(e1){}

	// 2) common paths
	var commonPaths = [
		'C:/toolcu/data/path.txt',
		'D:/toolcu/data/path.txt',
		Folder.desktop.fsName + '/toolcu/data/path.txt',
		Folder.desktop.fsName + '/toolcu/autotool/data/path.txt',
		Folder.desktop.fsName + '/autotool/data/path.txt',
		Folder.myDocuments.fsName + '/toolcu/data/path.txt'
	];
	for (var i = 0; i < commonPaths.length; i++) {
		possiblePaths.push(_norm(commonPaths[i]));
	}

	// Try each path
	for (var j = 0; j < possiblePaths.length; j++) {
		var p = possiblePaths[j];
		if (_fileExists(p)) {
			$.writeln('[getTimeline] Found path.txt at: ' + p);
			return p;
		}
	}
	return null;
}

// ===== Xác định thư mục data =====
var DATA_FOLDER = (function () {
	try {
		var targetDataPath = null;
		var rootDataPath = null;

		// ✅ 1) OVERRIDE from runAll (highest priority)
		try {
			if (typeof RUNALL_DATA_DIR !== 'undefined' && RUNALL_DATA_DIR) {
				rootDataPath = _norm(String(RUNALL_DATA_DIR));
				$.writeln('[DATA_FOLDER] Using RUNALL_DATA_DIR: ' + rootDataPath);
			}
			if (typeof RUNALL_DATA_FOLDER !== 'undefined' && RUNALL_DATA_FOLDER) {
				targetDataPath = _norm(String(RUNALL_DATA_FOLDER));
				$.writeln('[DATA_FOLDER] Using RUNALL_DATA_FOLDER: ' + targetDataPath);
			}
		} catch(eO){}

		// ✅ 2) path.txt
		if (!targetDataPath || !rootDataPath) {
			var pathTxt = _findPathTxt();
			if (pathTxt) {
				var cfg = _parsePathTxt(pathTxt);

				if (!rootDataPath && cfg && cfg.data_dir) {
					rootDataPath = _norm(String(cfg.data_dir));
					$.writeln('[DATA_FOLDER] Using data_dir from path.txt: ' + rootDataPath);
				}

				if (!targetDataPath) {
					if (cfg && cfg.data_folder) {
						var df = _norm(String(cfg.data_folder));
						// nếu absolute -> dùng luôn, không cần exists
						if (_isAbs(df)) {
							targetDataPath = df;
						} else if (rootDataPath) {
							targetDataPath = _norm(_joinPath(rootDataPath, df));
						}
					} else if (cfg && cfg.project_slug && rootDataPath) {
						targetDataPath = _norm(_joinPath(rootDataPath, String(cfg.project_slug)));
					}
				}
			}
		}

		// ✅ 3) Fallback: from script location => APP_ROOT/data (NEVER _internal/data)
		if (!rootDataPath) {
			var appRoot2 = _getAppRootDirFromScript();
			if (appRoot2) {
				rootDataPath = _norm(appRoot2.fsName + '/data');
				$.writeln('[DATA_FOLDER] Fallback rootDataPath from appRoot: ' + rootDataPath);
			} else {
				rootDataPath = _norm(Folder.desktop.fsName + '/toolcu/data');
				$.writeln('[DATA_FOLDER] Fallback rootDataPath to desktop: ' + rootDataPath);
			}
		}

		_ensureFolder(rootDataPath);

		if (!targetDataPath) targetDataPath = rootDataPath;

		_ensureFolder(targetDataPath);
		var folder = new Folder(targetDataPath);
		$.writeln('[DATA_FOLDER] Using data folder: ' + folder.fsName);
		return folder;
	} catch (e2) {
		$.writeln('[DATA_FOLDER] Fallback to desktop due to error: ' + e2);
		return Folder.desktop;
	}
})();

// --------- Utility Chuyển đổi Time ---------
function timeToSeconds(t) {
	try {
		if (!t) return 0;
		if (typeof t.seconds !== 'undefined') return t.seconds;
		if (typeof t.ticks !== 'undefined') {
			var TICKS_PER_SECOND = 254016000000;
			return t.ticks / TICKS_PER_SECOND;
		}
	} catch (e) {}
	return 0;
}

// --------- Lấy sequence hiện tại ---------
function getActiveSequence() {
	if (typeof app === 'undefined' || !app.project) {
		$.writeln('[getTimeline] Không ở trong Premiere.');
		return null;
	}
	var seq = app.project.activeSequence;
	if (!seq) $.writeln('[getTimeline] Không có activeSequence.');
	return seq;
}

// --------- Tìm track có clip được chọn ---------
function getSelectedVideoTrackIndices() {
	var seq = getActiveSequence();
	if (!seq) return [];
	var indices = [];
	if (!seq.videoTracks || seq.videoTracks.numTracks === 0) {
		$.writeln('[getTimeline] Không có video track.');
		return indices;
	}
	for (var i = 0; i < seq.videoTracks.numTracks; i++) {
		var vt = seq.videoTracks[i];
		if (!vt || !vt.clips || vt.clips.numItems === 0) continue;
		for (var c = 0; c < vt.clips.numItems; c++) {
			var clip = vt.clips[c];
			try {
				if (clip && typeof clip.isSelected === 'function' && clip.isSelected()) {
					indices.push(i);
					break;
				}
			} catch (e) {}
		}
	}
	$.writeln('[getTimeline] Track được chọn: ' + indices.join(', '));
	return indices;
}

function getTopmostSelectedVideoTrackIndex() {
	var sel = getSelectedVideoTrackIndices();
	if (!sel.length) return -1;
	var maxIdx = sel[0];
	for (var i = 1; i < sel.length; i++) if (sel[i] > maxIdx) maxIdx = sel[i];
	return maxIdx;
}

// fallback: top non-empty from top -> bottom
function findFirstNonEmptyVideoTrackIndex() {
	var seq = getActiveSequence();
	if (!seq || !seq.videoTracks) return -1;
	for (var i = seq.videoTracks.numTracks - 1; i >= 0; i--) {
		var vt = seq.videoTracks[i];
		if (vt && vt.clips && vt.clips.numItems > 0) {
			$.writeln('[fallback] Chọn top non-empty track index = ' + i + ' (total tracks=' + seq.videoTracks.numTracks + ')');
			return i;
		}
	}
	return -1;
}

function getVideoTrackClipsMetadata(trackIndex) {
	var seq = getActiveSequence();
	if (!seq) return [];
	if (trackIndex < 0 || trackIndex >= seq.videoTracks.numTracks) {
		$.writeln('[getTimeline] trackIndex không hợp lệ: ' + trackIndex);
		return [];
	}
	var vt = seq.videoTracks[trackIndex];
	if (!vt || !vt.clips) return [];

	function extractTextFromClip(clip) {
		if (!clip || !clip.projectItem) return '';
		try {
			if (typeof clip.projectItem.getComponents === 'function') {
				var comps = clip.projectItem.getComponents();
				if (comps && comps.numItems) {
					for (var ci = 0; ci < comps.numItems; ci++) {
						var comp = comps[ci];
						if (!comp || typeof comp.getParameters !== 'function') continue;
						var params = comp.getParameters();
						if (!params || !params.numItems) continue;
						for (var pi = 0; pi < params.numItems; pi++) {
							var p = params[pi];
							try {
								var dn = p.displayName || '';
								if (/text|source text|caption|contents/i.test(dn)) {
									if (typeof p.getValue === 'function') {
										var val = p.getValue();
										if (val && val.toString) {
											var s = val.toString();
											if (s) return s;
										}
									}
								}
							} catch(e1){}
						}
					}
				}
			}
		} catch(e2){}
		return '';
	}

	var list = [];
	for (var c = 0; c < vt.clips.numItems; c++) {
		var clip = vt.clips[c];
		if (!clip) continue;
		var item = {};
		try {
			item.name = clip.name || (clip.projectItem ? clip.projectItem.name : '');
			item.startSeconds = timeToSeconds(clip.start);
			item.endSeconds = timeToSeconds(clip.end);
			item.inPointSeconds = timeToSeconds(clip.inPoint);
			item.outPointSeconds = timeToSeconds(clip.outPoint);
			item.durationSeconds = item.endSeconds - item.startSeconds;
			item.indexInTrack = c;
			item.isSelected = (typeof clip.isSelected === 'function') ? clip.isSelected() : false;
			item.textContent = extractTextFromClip(clip);
		} catch (e) {
			item.error = '' + e;
		}
		list.push(item);
	}
	return list;
}

function getTopmostSelectedVideoTrackClips() {
	var idx = getTopmostSelectedVideoTrackIndex();
	if (idx < 0) {
		$.writeln('[getTimeline] Không có video track nào đang được chọn.');
		return [];
	}
	$.writeln('[getTimeline] Topmost selected video track index = ' + idx);
	return getVideoTrackClipsMetadata(idx);
}

function assertTopmostSelectedVideoTrackIsMax() {
	var sel = getSelectedVideoTrackIndices();
	if (!sel.length) {
		$.writeln('[getTimeline][TEST] FAIL: Không có track nào được chọn.');
		return false;
	}
	var top = getTopmostSelectedVideoTrackIndex();
	for (var i = 0; i < sel.length; i++) {
		if (sel[i] > top) {
			$.writeln('[getTimeline][TEST] FAIL: Tồn tại track cao hơn (' + sel[i] + ') > ' + top);
			return false;
		}
	}
	$.writeln('[getTimeline][TEST] PASS: Track ' + top + ' là lớn nhất trong các track đã chọn.');
	return true;
}

function getTopmostSelectedTrackClipsJSON(pretty) {
	var clips = getTopmostSelectedVideoTrackClips();
	try { return JSON.stringify(clips, null, pretty ? 2 : 0); } catch (e) { return '[]'; }
}

this.getTopmostSelectedVideoTrackClips = getTopmostSelectedVideoTrackClips;
this.getTopmostSelectedTrackClipsJSON = getTopmostSelectedTrackClipsJSON;
this.assertTopmostSelectedVideoTrackIsMax = assertTopmostSelectedVideoTrackIsMax;

// ========= FRAME RATE / TIMECODE =========
function getSequenceFrameRate() {
	var seq = getActiveSequence();
	if (!seq || typeof seq.getSettings !== 'function') return 25;
	try {
		var s = seq.getSettings();
		if (s && s.videoFrameRate && s.videoFrameRate.numerator && s.videoFrameRate.denominator) {
			return s.videoFrameRate.numerator / s.videoFrameRate.denominator;
		}
	} catch (e) {}
	return 25;
}
function secondsToTimecode(seconds, frameRate) {
	if (!frameRate) frameRate = getSequenceFrameRate();
	var totalFrames = Math.round(seconds * frameRate);
	if (totalFrames < 0) totalFrames = 0;
	var fps = Math.round(frameRate);
	var frames = totalFrames % fps;
	var totalSeconds = (totalFrames - frames) / fps;
	var s = totalSeconds % 60;
	var totalMinutes = (totalSeconds - s) / 60;
	var m = totalMinutes % 60;
	var h = (totalMinutes - m) / 60;
	function pad2(n) { return (n < 10 ? '0' : '') + n; }
	return pad2(h) + ':' + pad2(m) + ':' + pad2(s) + ':' + pad2(frames);
}

function getTrackClipRanges(trackIndex, opts) {
	opts = opts || {};
	var includeTC = !!opts.includeTimecode;
	var seq = getActiveSequence();
	if (!seq) return [];
	if (!seq.videoTracks || trackIndex < 0 || trackIndex >= seq.videoTracks.numTracks) {
		$.writeln('[getTimeline] getTrackClipRanges: trackIndex không hợp lệ ' + trackIndex);
		return [];
	}
	var vt = seq.videoTracks[trackIndex];
	if (!vt || !vt.clips) return [];
	var frameRate = getSequenceFrameRate();
	var list = [];
	var regex = null;
	if (opts.filterRegex) { try { regex = new RegExp(opts.filterRegex); } catch (e) {} }

	for (var c = 0; c < vt.clips.numItems; c++) {
		var clip = vt.clips[c];
		if (!clip) continue;
		if (opts.onlySelected && !(clip.isSelected && clip.isSelected())) continue;

		var name = '';
		try { name = clip.name || (clip.projectItem ? clip.projectItem.name : ''); } catch (e1) {}
		if (regex && !regex.test(name)) continue;

		var startS = timeToSeconds(clip.start);
		var endS = timeToSeconds(clip.end);

		var mediaPath = '';
		try { if (clip.projectItem && typeof clip.projectItem.getMediaPath === 'function') mediaPath = clip.projectItem.getMediaPath(); } catch(e2){}

		var textContent = '';
		try {
			if (clip.projectItem && typeof clip.projectItem.getComponents === 'function') {
				var comps2 = clip.projectItem.getComponents();
				if (comps2 && comps2.numItems) {
					for (var ci2 = 0; ci2 < comps2.numItems && !textContent; ci2++) {
						var comp2 = comps2[ci2];
						if (!comp2 || typeof comp2.getParameters !== 'function') continue;
						var params2 = comp2.getParameters();
						if (!params2 || !params2.numItems) continue;
						for (var pi2 = 0; pi2 < params2.numItems; pi2++) {
							var p2 = params2[pi2];
							try {
								var dn2 = p2.displayName || '';
								if (/text|source text|caption|contents/i.test(dn2) && typeof p2.getValue === 'function') {
									var val2 = p2.getValue();
									if (val2 && val2.toString) {
										var s2 = val2.toString();
										if (s2) { textContent = s2; break; }
									}
								}
							} catch(ee){}
						}
					}
				}
			}
		} catch(eTxt){}

		var obj = {
			indexInTrack: c,
			name: name,
			startSeconds: startS,
			endSeconds: endS,
			durationSeconds: endS - startS,
			mediaPath: mediaPath,
			textContent: textContent
		};
		if (includeTC) {
			obj.startTimecode = secondsToTimecode(startS, frameRate);
			obj.endTimecode = secondsToTimecode(endS, frameRate);
		}
		list.push(obj);
	}
	list.sort(function(a,b){ return a.startSeconds - b.startSeconds; });
	return list;
}

function runQuickTimelineTest(opts) {
	opts = opts || {};
	var usedProvidedTrack = (typeof opts.trackIndex === 'number');
	var trackIndex = usedProvidedTrack ? opts.trackIndex : getTopmostSelectedVideoTrackIndex();
	var fallbackUsed = false;
	var allowFallback = (opts.allowFallback !== false);

	if (trackIndex < 0 && !usedProvidedTrack && allowFallback) {
		trackIndex = findFirstNonEmptyVideoTrackIndex();
		if (trackIndex >= 0) {
			fallbackUsed = true;
			$.writeln('[runQuickTimelineTest] Fallback dùng track đầu tiên có clip: ' + trackIndex);
		}
	}
	if (trackIndex < 0) return { ok:false, reason:'NO_TRACK', fallbackTried: allowFallback };

	var ranges = getTrackClipRanges(trackIndex, { onlySelected: !!opts.onlySelected, includeTimecode: !!opts.includeTimecode });
	var pass = true;
	if (!usedProvidedTrack && !fallbackUsed) pass = assertTopmostSelectedVideoTrackIsMax();

	var exportResults = {};
	if (ranges.length && (opts.exportJSONPath || opts.exportCSVPath)) {
		function writeFile(path, content) {
			try {
				var f = new File(path);
				if (f.exists) { try { f.remove(); } catch (e5) {} }
				if (f.open('w')) { f.write(content); f.close(); return true; }
			} catch (e) { $.writeln('[EXPORT] Lỗi ghi ' + path + ': ' + e); }
			return false;
		}

		if (opts.exportJSONPath) {
			var jsonContent = JSON.stringify({ trackIndex: trackIndex, clips: ranges }, null, 2);
			exportResults.json = writeFile(opts.exportJSONPath, jsonContent);
			$.writeln('[EXPORT] JSON -> ' + opts.exportJSONPath + ' : ' + exportResults.json);
		}
		if (opts.exportCSVPath) {
			var haveTC = !!opts.includeTimecode;
			var header = haveTC
				? 'indexInTrack,name,startSeconds,endSeconds,durationSeconds,startTimecode,endTimecode,mediaPath,textContent'
				: 'indexInTrack,name,startSeconds,endSeconds,durationSeconds,mediaPath,textContent';
			var lines = [header];
			for (var i = 0; i < ranges.length; i++) {
				var r = ranges[i];
				function escCSV(s){
					s = (s || '').replace(/"/g,'""');
					if (s.indexOf(',') >= 0 || s.indexOf('\n') >= 0 || s.indexOf('\r') >= 0) s = '"' + s + '"';
					return s;
				}
				var name = escCSV(r.name);
				var media = escCSV(r.mediaPath);
				var txt = escCSV(r.textContent);
				if (haveTC) {
					lines.push([r.indexInTrack, name, r.startSeconds, r.endSeconds, r.durationSeconds, r.startTimecode||'', r.endTimecode||'', media, txt].join(','));
				} else {
					lines.push([r.indexInTrack, name, r.startSeconds, r.endSeconds, r.durationSeconds, media, txt].join(','));
				}
			}
			exportResults.csv = writeFile(opts.exportCSVPath, lines.join('\n'));
			$.writeln('[EXPORT] CSV -> ' + opts.exportCSVPath + ' : ' + exportResults.csv);
		}
	}
	return { ok: pass, trackIndex: trackIndex, ranges: ranges, exports: exportResults };
}

this.runQuickTimelineTest = runQuickTimelineTest;

// Auto-run export
(function(){
	try {
		var jsonPath = _norm(DATA_FOLDER.fsName + '/timeline_export.json');
		var csvPath  = _norm(DATA_FOLDER.fsName + '/timeline_export.csv');
		$.writeln('[auto-run] Xuất timeline ra: ' + jsonPath + ' và ' + csvPath);
		runQuickTimelineTest({
			onlySelected: false,
			exportJSONPath: jsonPath,
			exportCSVPath: csvPath
		});
	} catch(e) {
		$.writeln('[auto-run] Lỗi auto export: ' + e);
	}
})();
