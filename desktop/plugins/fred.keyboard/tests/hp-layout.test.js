// Laptop matching and physical geometry must not regress to a desktop board.
var assert = require("assert")
var fs = require("fs"), path = require("path")
var load = require("./load.js").loadQmlJs
var M = load("KeyboardModel.js"), R = load("LayoutResolver.js"), B = load("Bindings.js")
var layout = JSON.parse(fs.readFileSync(path.resolve(__dirname, "../layouts/hp-15-f233wm-us.json")))
var registry = JSON.parse(fs.readFileSync(path.resolve(__dirname, "../layouts/index.json")))
var device = { name: "AT Translated Set 2 keyboard", bus: "0011", vendor: "0001", product: "0001",
               systemVendor: "HP", systemSku: "L0T33UA#ABA" }
var resolved = R.resolve(device, registry)
assert.equal(resolved.layoutId, layout.id)
assert.equal(resolved.match, R.MATCH_SYSTEM)
assert.equal(resolved.kind, "reference-transcribed")
assert.equal(R.isExact(resolved), false) // references are not physical acceptance
;[{systemSku:"another SKU"}, {systemVendor:"another vendor"}, {bus:"0003"},
  {name:"External USB keyboard"}, {systemSku:""}].forEach(function (change) {
  assert.notEqual(R.resolve(Object.assign({},device,change),registry).layoutId,layout.id)
})
assert.equal(R.resolve(Object.assign({},device,{name:"Lenovo Calliope",vendor:"17ef",product:"608c",bus:"0003"}),registry).layoutId,"lenovo-calliope")
var cells = M.allCells(layout), ids = M.byId(layout), codes = M.byCode(layout)
assert.equal(cells.length,100)
assert.equal(new Set(cells.map(function(c){ return c.id })).size,100)
var emitted = cells.reduce(function(out,c){ return out.concat(M.cellCodes(c)) },[])
assert.equal(new Set(emitted).size, emitted.length)
assert.equal(ids.FN.code,null)
assert(!ids.RIGHTMETA && !ids.COMPOSE && !ids.SCROLLLOCK)
var rows = M.place(layout)
assert(rows[0].height < rows[1].height)
assert.equal(rows[5].placed.find(function(p){return p.cell.id==="UP"}).x,12.5)
assert.equal(rows[5].placed.find(function(p){return p.cell.id==="DOWN"}).x,12.5)
assert.equal(ids.UP.h,.5)
assert.equal(ids.DOWN.h,.5)
assert.equal(ids.DOWN.y,.5)
for(var i=1;i<6;i++) {
  assert.equal(M.mainBlockWidth(layout.rows[i]),14.5)
  var first = rows[i].placed.filter(function(p){return p.cell.id.indexOf("KP")===0 || p.cell.id==="NUMLOCK"})
  assert.equal(Math.min.apply(null,first.map(function(p){return p.x})),14.65)
  assert.equal(rows[i].width <= 18.65 + 1e-8,true)
}
// A real media event and its F-code resolve to one physical key, and its
// shortcut can be searched without appearing among the absent keys.
assert.equal(codes[113].id,"MUTE")
assert(M.cellCodes(ids.F6).includes(113))
var index = B.indexBinds([{kind:"key",key:"XF86AudioMute",cellId:B.keysymToCellId("XF86AudioMute"),modmask:0,dispatcher:"exec",arg:"volume mute"}],ids)
assert.equal(index.orphans.length,0)
assert.equal(B.lookup(index,{113:true}).length,1)
assert(B.keyTooltip(index,ids.F6,ids,codes).includes("volume mute"))
// Rectangles on each row may share a column only when vertically disjoint.
rows.forEach(function(row) {
  var placed = row.placed
  placed.forEach(function(a,i) {
    placed.slice(i+1).forEach(function(b) {
      var ay = a.cell.y || 0, by = b.cell.y || 0
      var ah = a.cell.h || row.height, bh = b.cell.h || row.height
      if(a.continued) ah=1
      if(b.continued) bh=1
      var horizontal = a.x < b.x+b.w-1e-8 && b.x < a.x+a.w-1e-8
      var vertical = ay < by+bh-1e-8 && by < ay+ah-1e-8
      assert(!(horizontal && vertical),a.cell.id+" overlaps "+b.cell.id)
    })
  })
})
console.log("ok - HP layout: exact SKU matching, 100 physical keys, split arrows, aligned numpad and media aliases")
