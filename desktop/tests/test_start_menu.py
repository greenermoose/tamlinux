"""Start menu model, geometry and isolated native input/layout checks."""
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import time
import unittest

DESKTOP = Path(__file__).resolve().parents[1]
MENU = DESKTOP / "shell/services/menu"


class ModelTests(unittest.TestCase):
    def evaluate(self, code):
        result = subprocess.run(["node", "-e", "const assert=require('assert'); const M=require(process.argv[1]); const S=require(process.argv[2]);" + code,
                                 str(MENU / "MenuModel.js"), str(MENU / "StartModel.js")], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_groups_preserve_user_actions_and_search_both_sections(self):
        self.evaluate("""
const source={quicklaunch:{},'quicklaunch.custom':{label:'My Editor',action:'custom --exact',aliases:['work']},
 'quicklaunch.reboot':{label:'Reboot',action:'DO NOT EXECUTE'},style:{},
 'style.theme':{label:'Theme',action:'theme-picker'},'style.text-size':{label:'Text Size',provider:'text-sizes'},
 'style.background':{label:'Background',action:'background-picker'},'style.bar':{},'style.bar.position':{},
 'style.bar.position.top':{action:'bar-top'}};
const m=M.mergeMenuSources(M.parseMenuJsonc(JSON.stringify(source)),[]);
let rows=S.rows(M,m.items,m.itemOrder,{}, {},'');
assert.deepEqual(rows.map(r=>r.section),['Quick Launch','Quick Launch','Settings','Settings','Settings','Settings']);
assert.equal(rows[0].action,'custom --exact'); assert(rows[1].separatorBefore);
assert.equal(rows[2].itemId,'style.theme'); assert.equal(rows[2].label,'Color Palette…');
assert.deepEqual(S.rows(M,m.items,m.itemOrder,{}, {},'work').map(r=>r.itemId),['quicklaunch.custom']);
assert.deepEqual(S.rows(M,m.items,m.itemOrder,{}, {},'palette').map(r=>r.itemId),['style.theme']);
assert.equal(S.rows(M,m.items,m.itemOrder,{}, {},'missing').length,0);
assert.equal(M.resolveRoute(m.items,m.itemOrder,'quicklaunch'),'quicklaunch');
assert.equal(m.items['style.theme'].label,'Theme');
""")

    def test_guarded_entries_and_long_extensions(self):
        self.evaluate("""
const source={quicklaunch:{}};
for(let i=0;i<100;i++) source['quicklaunch.app'+i]={label:'App '+i,action:'safe '+i,when:'condition'};
const m=M.mergeMenuSources(M.parseMenuJsonc(JSON.stringify(source)),[]);
const rows=S.rows(M,m.items,m.itemOrder,{'quicklaunch.app4':false},{},'');
assert.equal(rows.length,99); assert.equal(rows[4].itemId,'quicklaunch.app5');
assert.equal(rows[98].action,'safe 99');
""")

    def test_product_starter_list_yields_to_user_tree(self):
        self.evaluate("""
const fs=require('fs');
const defaults=M.parseMenuJsonc(fs.readFileSync(process.argv[3],'utf8'));
const user=M.parseMenuJsonc(JSON.stringify({quicklaunch:{aliases:['mine']},'quicklaunch.personal':{label:'Personal',action:'exact --argv'}}));
let m=M.mergeMenuSources(S.defaultsFor(defaults,user),user);
assert.deepEqual(m.itemOrder.filter(id=>m.items[id].parent==='quicklaunch'),['quicklaunch.personal']);
assert.equal(M.resolveRoute(m.items,m.itemOrder,'mine'),'quicklaunch');
assert.equal(S.rows(M,m.items,m.itemOrder,{}, {},'')[0].action,'exact --argv');
m=M.mergeMenuSources(S.defaultsFor(defaults,[]),[]);
assert(m.items['quicklaunch.browser']);
assert(M.isVisible(m.items,m.itemOrder,{},m.items.start));
""".replace("process.argv[3]", json.dumps(str(DESKTOP / 'menu/default.jsonc'))))

    def test_output_origins_scaling_coordinates_and_edges(self):
        self.evaluate("""
const screens=[{name:'left',x:-1280,y:-100,width:1280,height:720},
 {name:'right',x:0,y:0,width:960,height:540}];
assert.equal(S.screenAt(screens,-100,0).name,'left');
assert.equal(S.screenAt(screens,0,0).name,'right');
assert.equal(S.screenAt(screens,960,540),null);
assert.equal(S.screenAt(screens,NaN,4),null);
for(const anchor of [{x:0,y:0},{x:1279,y:719},{x:600,y:700},{x:1,y:694,edge:'bottom'}]) {
 const p=S.placement(1280,720,320,530,anchor,8);
 assert(p.x>=8 && p.x+320<=1272); assert(p.y>=8 && p.y+530<=712);
}
assert.deepEqual(S.placement(1280,720,320,530,{x:20,y:26,edge:'top'},8),{x:20,y:26});
assert.deepEqual(S.placement(1280,720,320,530,{x:20,y:694,edge:'bottom'},8),{x:20,y:164});
""")


@unittest.skipUnless(shutil.which('sway') and shutil.which('quickshell'), 'headless Sway and Quickshell required')
class NativeTests(unittest.TestCase):
    def test_start_layout_navigation_appearance_and_bar_input(self):
        with tempfile.TemporaryDirectory(prefix='start-menu-') as directory:
            root = Path(directory)
            archive = subprocess.check_output(['git','archive','HEAD','desktop/shell'],cwd=DESKTOP.parent)
            with tarfile.open(fileobj=io.BytesIO(archive)) as tree:
                tree.extractall(root,filter='data')
            shell=root/'desktop/shell'
            shutil.copytree(MENU,shell/'services/menu',dirs_exist_ok=True)
            for name in ['BarApi.qml','BarWindow.qml','BarLayout.qml','Compositor.qml','HyprlandAdapter.qml']:
                shutil.copy2(DESKTOP/'shell/host'/name,shell/'host'/name)
            defaults=root/'defaults.jsonc'
            source={'start':{'label':'Start'},'quicklaunch':{'label':'Quick Launch'},'style':{},
                    'style.theme':{'label':'Theme','action':'echo theme'},
                    'style.text-size':{'label':'Text Size','provider':'text-sizes'},
                    'style.background':{'label':'Background','action':'echo background'},
                    'style.bar':{},'style.bar.position':{},'style.bar.position.top':{'action':'echo top'}}
            for i in range(11): source['quicklaunch.app'+str(i)]={'label':'App '+str(i),'action':'echo app'+str(i)}
            defaults.write_text(json.dumps(source))
            extension=root/'extension.jsonc';extension.write_text('{}')
            fixture=(DESKTOP/'fixtures/start-menu/shell.qml').read_text().replace('__DEFAULT__',json.dumps(str(defaults))).replace('__EXTENSION__',json.dumps(str(extension)))
            (shell/'proof-start.qml').write_text(fixture)
            runtime=root/'runtime';runtime.mkdir(mode=0o700)
            env={'PATH':'/usr/bin','HOME':directory,'XDG_CONFIG_HOME':directory,'XDG_CACHE_HOME':directory,
                 'XDG_STATE_HOME':directory,'XDG_RUNTIME_DIR':str(runtime),'QML_IMPORT_PATH':str(shell/'modules'),
                 'QSG_RENDER_LOOP':'basic','TAMLINUX_BAR_EXCLUSIVE':'1'}
            if os.environ.get('START_MENU_SCREENSHOT'):
                env['START_MENU_SCREENSHOT'] = os.environ['START_MENU_SCREENSHOT']
            config=root/'sway.conf';config.write_text('output HEADLESS-1 resolution 1280x720 position 0 0\noutput HEADLESS-2 resolution 1920x1080 scale 1.5 position -1280 0\n')
            with (root/'sway.log').open('w') as log:
                sway=subprocess.Popen(['/usr/bin/sway','-c',str(config)],env=dict(env,WLR_BACKENDS='headless',WLR_HEADLESS_OUTPUTS='2',WLR_LIBINPUT_NO_DEVICES='1',WLR_RENDERER='pixman'),stdout=log,stderr=subprocess.STDOUT)
                try:
                    deadline=time.monotonic()+5;socket=None
                    while time.monotonic()<deadline and sway.poll() is None:
                        socket=next((p for p in runtime.glob('wayland-*') if not p.name.endswith('.lock')),None)
                        if socket: break
                        time.sleep(0.05)
                    self.assertIsNotNone(socket,(root/'sway.log').read_text())
                    env.update(WAYLAND_DISPLAY=socket.name,QT_QPA_PLATFORM='wayland')
                    result=subprocess.run(['/usr/bin/quickshell','--no-color','-p',str(shell/'proof-start.qml')],env=env,capture_output=True,text=True,timeout=20)
                finally:
                    sway.terminate();sway.wait(timeout=5)
            output=result.stdout+result.stderr
            self.assertEqual(result.returncode,0,output)
            self.assertIn('START_MENU_OK',output)
            self.assertEqual(output.count('action-recorded open-start HEADLESS-1'), 1, output)
            for error in ['ReferenceError','TypeError','Binding loop','START_FAILED','Required property']:
                self.assertNotIn(error,output)
