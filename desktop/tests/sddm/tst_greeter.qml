import QtQuick
import QtTest
import "../../native/integration/sddm" as Greeter

Item {
    width: 800
    height: 600
    ListModel {
        id: sessionModel
        property int lastIndex: 0
    }
    QtObject { id: userModel; property string lastUser: "tester" }
    QtObject {
        id: sddm
        property var calls: []
        signal loginFailed()
        signal loginSucceeded()
        function login(user, password, index) {
            calls = calls.concat([{user: user, password: password, index: index}])
        }
    }
    Component { id: theme; Greeter.Main {} }
    TestCase {
        name: "NativeGreeter"
        when: windowShown
        property var greeter
        function init() {
            sessionModel.clear()
            sessionModel.append({name: "Hyprland (inherited)", file: "/usr/local/share/wayland-sessions/hyprland-tamlinux.desktop"})
            sessionModel.append({name: "Tamlinux (Hyprland)", file: "/usr/share/wayland-sessions/tamlinux.desktop"})
            sessionModel.lastIndex = 0
            userModel.lastUser = "tester"
            sddm.calls = []
            greeter = createTemporaryObject(theme, parent)
            verify(greeter)
        }
        function control(name) { return findChild(greeter, name) }
        function test_visible_choice_reaches_login() {
            var selector = control("session")
            verify(selector.visible)
            compare(selector.currentText, "Hyprland (inherited)")
            mouseClick(selector)
            tryCompare(selector.popup, "opened", true)
            var choice = selector.popup.contentItem.itemAtIndex(1)
            verify(choice)
            mouseClick(choice)
            compare(selector.currentIndex, 1)
            compare(selector.currentText, "Tamlinux (Hyprland)")
            var password = control("password")
            password.text = "mock secret"
            password.forceActiveFocus()
            keyClick(Qt.Key_Return)
            compare(sddm.calls.length, 1)
            compare(sddm.calls[0].index, 1)
            compare(sddm.calls[0].user, "tester")
            compare(sddm.calls[0].password, "mock secret")
            compare(password.text, "")
            greeter.login()
            compare(sddm.calls.length, 1)
        }
        function test_keyboard_selection_and_retry() {
            var selector = control("session")
            selector.forceActiveFocus()
            keyClick(Qt.Key_Down)
            compare(selector.currentIndex, 1)
            keyClick(Qt.Key_Tab)
            verify(control("password").activeFocus)
            control("password").text = "bad"
            keyClick(Qt.Key_Return)
            sddm.loginFailed()
            compare(greeter.authenticating, false)
            compare(control("password").text, "")
            verify(control("password").activeFocus)
            verify(control("message").text.length > 0)
            compare(selector.currentIndex, 1)
            control("password").text = "retry"
            mouseClick(control("submit"))
            compare(sddm.calls.length, 2)
            compare(sddm.calls[1].index, 1)
            sddm.loginSucceeded()
            compare(control("message").text, "")
        }
        function test_missing_sessions_or_user_refuse_login() {
            control("username").text = "  "
            greeter.login()
            compare(sddm.calls.length, 0)
            control("username").text = "another-user"
            sessionModel.clear()
            compare(control("session").currentIndex, -1)
            greeter.login()
            compare(sddm.calls.length, 0)
            verify(!control("submit").enabled)
            compare(control("message").text, "No desktop sessions are installed.")
        }
        function test_stale_saved_index_is_bounded() {
            sessionModel.lastIndex = 99
            var other = createTemporaryObject(theme, parent)
            verify(other)
            compare(findChild(other, "session").currentIndex, 1)
        }
        function test_small_screen_and_username_focus() {
            userModel.lastUser = ""
            var other = createTemporaryObject(theme, parent, {width: 640, height: 480})
            verify(other)
            verify(findChild(other, "username").activeFocus)
            var form = findChild(other, "loginForm")
            verify(form.x >= 0 && form.y >= 0)
            verify(form.x + form.width <= other.width)
            verify(form.y + form.height <= other.height)
        }
    }
}
