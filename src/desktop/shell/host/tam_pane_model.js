// Pure parsers and snapshot builders for TamPaneAdapter.qml.
// No QML, process, or compositor imports.

var outputLimit = 64;
var tagCount = 9;
var windowLimit = 8;
var titleLimit = 80;
var classLimit = 64;
var descriptionLimit = 128;
var keymapLimit = 128;
var keyboardLimit = 16;
var bindsLimit = 262144;
var maxBinds = 4096;

function validName(value) {
  return typeof value === "string" && /^[A-Za-z0-9._-]{1,64}$/.test(value);
}

function validAppName(value) {
  return typeof value === "string" && /^[A-Za-z0-9][A-Za-z0-9 ._+-]{0,63}$/.test(value);
}

function validTag(value) {
  return /^(?:[1-9])$/.test(String(value === undefined || value === null ? "" : value));
}

function boundedPosition(value) {
  var n = Number(value);
  if (!isFinite(n)) return 0;
  n = Math.round(n);
  if (n > 100000) return 100000;
  if (n < -100000) return -100000;
  return n;
}

function boundedText(value, limit) {
  var text = String(value === undefined || value === null ? "" : value);
  text = text.replace(/\r/g, " ").replace(/\n/g, " ");
  return text.length > limit ? text.substring(0, limit) : text;
}

function unescapeField(raw) {
  var s = String(raw || "");
  var out = "";
  for (var i = 0; i < s.length; i++) {
    if (s.charAt(i) === "\\" && i + 1 < s.length) {
      var next = s.charAt(i + 1);
      if (next === "\\") { out += "\\"; i++; continue; }
      if (next === "t") { out += "\t"; i++; continue; }
      if (next === "n") { out += "\n"; i++; continue; }
      if (next === "r") { out += "\r"; i++; continue; }
    }
    out += s.charAt(i);
  }
  return out;
}

function parseLine(line) {
  var parts = String(line || "").split("\t");
  if (parts.length === 0 || parts[0] === "") return null;
  var kind = parts[0];
  var start = 1;
  var eventKind = "";
  if (kind === "event") {
    if (parts.length < 2) return null;
    eventKind = parts[1];
    start = 2;
  }
  var fields = {};
  for (var i = start; i < parts.length; i++) {
    var eq = parts[i].indexOf("=");
    if (eq <= 0) continue;
    var k = parts[i].substring(0, eq);
    var v = unescapeField(parts[i].substring(eq + 1));
    fields[k] = v;
  }
  return { kind: kind, eventKind: eventKind, fields: fields };
}

function maskToTagIds(mask) {
  var n = Number(mask);
  if (!isFinite(n) || n <= 0) return [];
  var ids = [];
  for (var t = 1; t <= tagCount; t++) {
    if ((n & (1 << (t - 1))) !== 0) ids.push(t);
  }
  return ids;
}

function parseMonitors(lines) {
  var list = [];
  var seen = {};
  for (var i = 0; i < (lines || []).length && list.length < outputLimit; i++) {
    var rec = parseLine(lines[i]);
    if (!rec || rec.kind !== "monitor") continue;
    var name = rec.fields.name || "";
    if (!validName(name) || seen["$" + name]) continue;
    seen["$" + name] = true;
    var mask = parseInt(rec.fields.tags || "0", 10);
    if (!isFinite(mask) || mask < 0) mask = 0;
    var activeIds = maskToTagIds(mask);
    list.push({
      name: name,
      x: boundedPosition(rec.fields.x),
      y: boundedPosition(rec.fields.y),
      width: boundedPosition(rec.fields.w),
      height: boundedPosition(rec.fields.h),
      focused: rec.fields.focused === "1",
      dpmsOn: rec.fields.dpms !== "0",
      description: boundedText(rec.fields.description || "", descriptionLimit),
      tagMask: mask,
      activeWorkspaceIds: activeIds,
      activeWorkspaceId: activeIds.length > 0 ? activeIds[0] : 0,
      special: false
    });
  }
  list.sort(function(a, b) { return a.name < b.name ? -1 : a.name > b.name ? 1 : 0; });
  return list;
}

function parseTags(lines) {
  var map = {};
  for (var i = 0; i < (lines || []).length; i++) {
    var rec = parseLine(lines[i]);
    if (!rec || rec.kind !== "tag") continue;
    var mon = rec.fields.monitor || "";
    if (!validName(mon)) continue;
    var view = parseInt(rec.fields.view || "0", 10);
    var occupied = parseInt(rec.fields.occupied || "0", 10);
    map[mon] = {
      view: isFinite(view) && view >= 0 ? view : 0,
      occupied: isFinite(occupied) && occupied >= 0 ? occupied : 0,
      focused: rec.fields.focused === "1"
    };
  }
  return map;
}

function parseWindows(lines) {
  var list = [];
  for (var i = 0; i < (lines || []).length; i++) {
    var rec = parseLine(lines[i]);
    if (!rec || rec.kind !== "window") continue;
    var mon = rec.fields.monitor || "";
    if (!validName(mon)) continue;
    var tags = parseInt(rec.fields.tags || "0", 10);
    if (!isFinite(tags) || tags < 0) tags = 0;
    var cls = boundedText(rec.fields.app_id || "", classLimit);
    var title = String(rec.fields.title || "").replace(/\r/g, " ").replace(/\n/g, " ");
    if (title.length > titleLimit) title = title.substring(0, titleLimit - 3) + "...";
    list.push({
      monitor: mon,
      tags: tags,
      focused: rec.fields.focused === "1",
      floating: rec.fields.floating === "1",
      fullscreen: rec.fields.fullscreen === "1",
      scratchpad: rec.fields.scratchpad === "1",
      className: cls,
      title: title
    });
  }
  return list;
}

function parseCursor(lines) {
  for (var i = 0; i < (lines || []).length; i++) {
    var rec = parseLine(lines[i]);
    if (!rec || rec.kind !== "cursor") continue;
    var x = Number(rec.fields.x);
    var y = Number(rec.fields.y);
    if (isFinite(x) && isFinite(y)) return { x: x, y: y };
  }
  return null;
}

function parseKeyboards(lines) {
  var keyboards = [];
  var mainKeymap = "";
  var fallbackKeymap = "";
  for (var i = 0; i < (lines || []).length && keyboards.length < keyboardLimit; i++) {
    var rec = parseLine(lines[i]);
    if (!rec || rec.kind !== "keyboard") continue;
    var name = rec.fields.name || "";
    if (!validName(name)) continue;
    var activeKeymap = boundedText(rec.fields.active_keymap || "", keymapLimit);
    var layoutRaw = rec.fields.layout;
    var layout = layoutRaw === undefined || layoutRaw === "" ? null : boundedText(layoutRaw, keymapLimit);
    var idx = parseInt(rec.fields.active_layout_index || "0", 10);
    var isMain = rec.fields.main === "1";
    keyboards.push({
      name: name,
      layout: layout,
      activeKeymap: activeKeymap,
      activeLayoutIndex: isFinite(idx) && idx >= 0 ? idx : 0,
      main: isMain
    });
    if (activeKeymap !== "") {
      if (isMain) mainKeymap = activeKeymap;
      if (fallbackKeymap === "") fallbackKeymap = activeKeymap;
    }
  }
  return {
    keyboards: keyboards,
    activeKeymap: mainKeymap || fallbackKeymap
  };
}

function modmaskFromNames(modsText) {
  if (!modsText || modsText === "none") return 0;
  var mask = 0;
  var parts = String(modsText).split("+");
  for (var i = 0; i < parts.length; i++) {
    var m = parts[i].trim().toLowerCase();
    if (m === "shift") mask |= 1;
    else if (m === "ctrl" || m === "control") mask |= 4;
    else if (m === "alt" || m === "mod1") mask |= 8;
    else if (m === "meta" || m === "super" || m === "mod4") mask |= 64;
  }
  return mask;
}

// Convert tam-pane `binds` lines into the JSON array consumed by KeybindingsModel.parseBinds.
function parseBindsToJson(lines) {
  var out = [];
  for (var i = 0; i < (lines || []).length && out.length < maxBinds; i++) {
    var rec = parseLine(lines[i]);
    if (!rec || rec.kind !== "bind") continue;
    var key = String(rec.fields.key || "").trim();
    if (key === "") continue;
    var action = String(rec.fields.action || "").trim();
    var sp = action.indexOf(" ");
    var dispatcher = sp >= 0 ? action.substring(0, sp) : action;
    var arg = sp >= 0 ? action.substring(sp + 1).trim() : "";
    out.push({
      modmask: modmaskFromNames(rec.fields.mods || ""),
      key: key,
      description: action,
      dispatcher: dispatcher,
      arg: arg
    });
  }
  var json = JSON.stringify(out);
  return json.length > bindsLimit ? "[]" : json;
}

function buildIpcSnapshot(state) {
  var monitors = state.monitors || [];
  var tagMap = state.tags || {};
  var windows = state.windows || [];
  var focusedOutput = "";
  var focusedWorkspace = 0;

  var outputs = monitors.map(function(mon) {
    var tagInfo = tagMap[mon.name];
    var viewMask = tagInfo ? tagInfo.view : mon.tagMask;
    var activeIds = maskToTagIds(viewMask);
    var activeId = activeIds.length > 0 ? activeIds[0] : 0;
    var focused = tagInfo ? tagInfo.focused : mon.focused;
    if (focused && focusedOutput === "") {
      focusedOutput = mon.name;
      focusedWorkspace = activeId;
    }
    return {
      name: mon.name,
      focused: focused,
      activeWorkspaceId: activeId,
      activeWorkspaceIds: activeIds,
      tagMask: viewMask,
      dpmsOn: mon.dpmsOn !== false,
      description: mon.description || "",
      x: mon.x,
      y: mon.y,
      special: false
    };
  });

  // Expand windows across every tag bit they belong to on their output.
  var byOutputTag = {};
  for (var w = 0; w < windows.length; w++) {
    var win = windows[w];
    if (!win || win.scratchpad) continue;
    var winTags = maskToTagIds(win.tags);
    for (var ti = 0; ti < winTags.length; ti++) {
      var bucketKey = win.monitor + ":" + winTags[ti];
      if (!byOutputTag[bucketKey]) byOutputTag[bucketKey] = [];
      if (byOutputTag[bucketKey].length < windowLimit && (win.className !== "" || win.title !== "")) {
        byOutputTag[bucketKey].push({ className: win.className, title: win.title });
      }
    }
  }

  var workspaces = [];
  for (var o = 0; o < outputs.length; o++) {
    var out = outputs[o];
    var info = tagMap[out.name];
    var occMask = info ? info.occupied : 0;
    for (var t = 1; t <= tagCount; t++) {
      var bit = 1 << (t - 1);
      var list = byOutputTag[out.name + ":" + t] || [];
      workspaces.push({
        id: t,
        output: out.name,
        active: (out.tagMask & bit) !== 0,
        urgent: false,
        occupied: list.length > 0 || (occMask & bit) !== 0,
        windows: list
      });
    }
  }

  return {
    outputs: outputs,
    focusedOutputName: focusedOutput,
    workspaces: workspaces,
    focusedWorkspaceId: focusedWorkspace,
    bindingsText: state.bindingsText || "",
    activeKeymap: state.activeKeymap || ""
  };
}
