// Loads a QML .js module into Node for testing.
//
// QML data modules start with `.pragma library`, which marks them as shared
// and stateless to the QML engine. Node's parser rejects that line, so we
// strip it and evaluate the rest in a module scope. The source file stays
// valid QML - we do not weaken the real code to make it testable.

var fs = require("fs")
var path = require("path")
var vm = require("vm")

function loadQmlJs(relPath) {
  var file = path.resolve(__dirname, "..", relPath)
  var src = fs.readFileSync(file, "utf8")

  // Strip QML-only pragmas. They are always leading lines.
  var cleaned = src.replace(/^\s*\.pragma\s+library\s*$/gm, "")
                   .replace(/^\s*\.import\s+.*$/gm, "")

  var module_ = { exports: {} }
  var sandbox = { module: module_, exports: module_.exports, console: console }
  vm.createContext(sandbox)
  vm.runInContext(cleaned, sandbox, { filename: file })
  return module_.exports
}

module.exports = { loadQmlJs: loadQmlJs }
