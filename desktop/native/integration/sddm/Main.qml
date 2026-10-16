// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

Rectangle {
    id: root
    width: 640
    height: 480
    color: "#182028"
    property bool authenticating: false
    property string message: ""

    function login() {
        if (authenticating || !username.text.trim() || session.currentIndex < 0
                || session.currentIndex >= session.count)
            return
        message = ""
        authenticating = true
        sddm.login(username.text.trim(), password.text, session.currentIndex)
        password.clear()
    }

    Connections {
        target: sddm
        function onLoginFailed() {
            root.authenticating = false
            root.message = qsTr("Login failed. Check your username and password.")
            password.clear()
            password.forceActiveFocus()
        }
        function onLoginSucceeded() {
            root.message = ""
            password.clear()
        }
    }

    ColumnLayout {
        id: form
        objectName: "loginForm"
        anchors.centerIn: parent
        width: Math.min(420, root.width - 48)
        spacing: 12
        enabled: !root.authenticating

        Label {
            text: "Tamlinux"
            color: "#f1f4f6"
            font.pixelSize: 32
            Layout.bottomMargin: 8
        }
        Label { text: qsTr("Username"); color: "#f1f4f6" }
        TextField {
            id: username
            objectName: "username"
            Layout.fillWidth: true
            text: userModel.lastUser
            Accessible.name: qsTr("Username")
            selectByMouse: true
            KeyNavigation.tab: session
            onAccepted: password.forceActiveFocus()
        }
        Label { text: qsTr("Session"); color: "#f1f4f6" }
        ComboBox {
            id: session
            objectName: "session"
            Layout.fillWidth: true
            model: sessionModel
            textRole: "name"
            Accessible.name: qsTr("Session")
            KeyNavigation.tab: password
            Component.onCompleted: currentIndex = count ? Math.max(0, Math.min(sessionModel.lastIndex, count - 1)) : -1
        }
        Label { text: qsTr("Password"); color: "#f1f4f6" }
        TextField {
            id: password
            objectName: "password"
            Layout.fillWidth: true
            Accessible.name: qsTr("Password")
            echoMode: TextInput.Password
            inputMethodHints: Qt.ImhSensitiveData | Qt.ImhNoPredictiveText
            selectByMouse: true
            KeyNavigation.tab: submit
            onAccepted: root.login()
        }
        Button {
            id: submit
            objectName: "submit"
            Layout.fillWidth: true
            text: root.authenticating ? qsTr("Logging in…") : qsTr("Log in")
            enabled: username.text.trim().length > 0 && session.currentIndex >= 0
                     && session.currentIndex < session.count
            KeyNavigation.tab: username
            onClicked: root.login()
        }
        Label {
            objectName: "message"
            Layout.fillWidth: true
            color: "#ffc9c9"
            text: session.count ? root.message : qsTr("No desktop sessions are installed.")
            wrapMode: Text.WordWrap
            Accessible.role: Accessible.AlertMessage
        }
    }
    Component.onCompleted: {
        if (username.text.length)
            password.forceActiveFocus()
        else
            username.forceActiveFocus()
    }
}
