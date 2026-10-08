// Shared protocol facts. No compositor imports, processes, or global focus guesses.
var listLimit = 64;

function validName(value) {
  return typeof value === "string" && /^[A-Za-z0-9._-]{1,64}$/.test(value);
}

function workspaceNumber(value) {
  var text = String(value === undefined || value === null ? "" : value);
  return /^(?:[1-9]|10)$/.test(text) ? Number(text) : 0;
}

function position(value) {
  return typeof value === "number" && isFinite(value)
    ? Math.max(-100000, Math.min(100000, Math.round(value))) : 0;
}

function label(value) {
  return String(value || "").replace(/[\r\n]/g, " ").substring(0, 128);
}

function snapshot(sets, screens) {
  sets = sets || [];
  screens = screens || [];
  var outputs = [];
  var names = {};
  var problems = [];
  if (sets.length > listLimit || screens.length > listLimit) problems.push("list-limit");
  for (var i = 0; i < screens.length && i < listLimit; i++) {
    var screen = screens[i];
    if (!screen || !validName(screen.name) || names["$" + screen.name]) {
      problems.push("invalid-output");
      continue;
    }
    var output = { name: screen.name, x: position(screen.x), y: position(screen.y),
      width: position(screen.width), height: position(screen.height),
      description: label(screen.model), activeWorkspaceId: 0 };
    outputs.push(output);
    names["$" + screen.name] = output;
  }
  var spaces = [];
  var ids = {};
  for (var w = 0; w < sets.length && w < listLimit; w++) {
    var set = sets[w];
    if (!set) continue;
    // ext-workspace ids are opaque. Numeric user-facing names come first.
    var number = workspaceNumber(set.name);
    if (!number) continue;
    if (ids["$" + number]) {
      problems.push("duplicate-workspace");
      continue;
    }
    ids["$" + number] = true;
    var projected = set.projection ? set.projection.screens : [];
    projected = projected || [];
    // A facade workspace has one owner. Never invent one for a shared group.
    var owner = projected.length === 1 && projected[0] && validName(projected[0].name)
      && names["$" + projected[0].name] ? projected[0].name : "";
    if (!owner) problems.push("workspace-projection");
    var active = set.active === true;
    if (active && owner) {
      if (names["$" + owner].activeWorkspaceId) problems.push("multiple-active-workspaces");
      else names["$" + owner].activeWorkspaceId = number;
    }
    spaces.push({ id: number, output: owner, active: active, urgent: set.urgent === true,
      canActivate: set.canActivate === true, canSetProjection: set.canSetProjection === true });
  }
  outputs.sort(function(a, b) { return a.name < b.name ? -1 : a.name > b.name ? 1 : 0; });
  spaces.sort(function(a, b) { return a.id - b.id; });
  return { outputs: outputs, workspaces: spaces, ready: outputs.length > 0 && spaces.length > 0
    && problems.length === 0, problems: problems.slice(0, listLimit) };
}

// Add only IPC-only fields. The protocol does not report global focus, DPMS,
// special workspaces, window membership, or keyboard/binding information.
function combine(protocol, ipc) {
  if (!protocol || !protocol.ready) return ipc;
  var outputs = protocol.outputs.map(function(output) {
    var gap = (ipc.outputs || []).filter(function(item) { return item.name === output.name; })[0] || {};
    return { name: output.name, x: output.x, y: output.y,
      description: output.description, activeWorkspaceId: output.activeWorkspaceId,
      focused: output.name === ipc.focusedOutputName, dpmsOn: gap.dpmsOn !== false,
      special: gap.special === true };
  });
  var workspaces = protocol.workspaces.map(function(space) {
    var gap = (ipc.workspaces || []).filter(function(item) { return item.id === space.id; })[0] || {};
    return { id: space.id, output: space.output, occupied: gap.occupied === true,
      windows: gap.windows || [] };
  });
  return { outputs: outputs, workspaces: workspaces, focusedOutputName: ipc.focusedOutputName,
    focusedWorkspaceId: ipc.focusedWorkspaceId, bindingsText: ipc.bindingsText,
    activeKeymap: ipc.activeKeymap };
}

function comparable(state) {
  return {
    outputs: (state.outputs || []).slice(0, listLimit).map(function(output) {
      return { name: output.name, x: output.x, y: output.y,
        activeWorkspaceId: workspaceNumber(output.activeWorkspaceId) };
    }).sort(function(a, b) { return a.name < b.name ? -1 : a.name > b.name ? 1 : 0; }),
    workspaces: (state.workspaces || []).slice(0, listLimit).filter(function(space) {
      return workspaceNumber(space.id) !== 0;
    }).map(function(space) { return { id: space.id, output: space.output }; })
      .sort(function(a, b) { return a.id - b.id; })
  };
}

function compare(protocol, ipc) {
  if (!protocol || !protocol.ready || !ipc) return { equal: false, differences: ["not-ready"] };
  var left = comparable(protocol);
  var right = comparable(ipc);
  var differences = [];
  if (JSON.stringify(left.outputs) !== JSON.stringify(right.outputs)) differences.push("outputs");
  if (JSON.stringify(left.workspaces) !== JSON.stringify(right.workspaces)) differences.push("workspaces");
  return { equal: differences.length === 0, differences: differences };
}
