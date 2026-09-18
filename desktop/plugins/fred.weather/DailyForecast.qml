import QtQuick
import qs.Commons
import "Model.js" as Model

Column {
  id: root
  required property var days
  required property color foreground
  required property string fontFamily
  required property bool useImperial

  width: parent.width
  spacing: Style.space(8)

  Text {
    text: "10-DAY OUTLOOK"
    color: root.foreground
    font.family: root.fontFamily
    font.pixelSize: Style.font.bodySmall
    font.letterSpacing: 1
    anchors.left: parent.left
  }

  Column {
    width: parent.width
    spacing: Style.space(4)

    Repeater {
      model: root.days || []
      Rectangle {
        required property var modelData
        required property int index
        width: parent.width
        height: Style.space(34)
        radius: Style.cornerRadius
        color: rowMouse.containsMouse ? Style.hoverFillFor(root.foreground, Color.accent) : "transparent"

        MouseArea {
          id: rowMouse
          anchors.fill: parent
          hoverEnabled: true
        }

        Row {
          anchors.fill: parent
          anchors.leftMargin: Style.space(8)
          anchors.rightMargin: Style.space(8)
          spacing: Style.space(8)

          // 1. Day label (Today, Tomorrow, Sat Sep 20)
          Text {
            width: Style.space(100)
            anchors.verticalCenter: parent.verticalCenter
            text: modelData.dayLabel || ""
            color: root.foreground
            font.family: root.fontFamily
            font.pixelSize: Style.font.body
            font.bold: modelData.isToday === true
          }

          // 2. Weather Icon
          Text {
            width: Style.space(30)
            anchors.verticalCenter: parent.verticalCenter
            horizontalAlignment: Text.AlignHCenter
            text: Model.dayIcon(modelData)
            color: root.foreground
            font.family: root.fontFamily
            font.pixelSize: Style.font.title
          }

          // 3. Condition Description
          Text {
            width: Style.space(140)
            anchors.verticalCenter: parent.verticalCenter
            elide: Text.ElideRight
            text: modelData.description || ""
            color: root.foreground
            font.family: root.fontFamily
            font.pixelSize: Style.font.bodySmall
            opacity: 0.8
          }

          // 4. Rain Chance Badge
          Text {
            width: Style.space(70)
            anchors.verticalCenter: parent.verticalCenter
            textFormat: Text.PlainText
            text: (modelData.precipitationProbability !== null && modelData.precipitationProbability !== undefined)
              ? ("\uf043 " + modelData.precipitationProbability + "%") : ""
            color: (modelData.precipitationProbability && modelData.precipitationProbability >= 40)
              ? Color.accent : root.foreground
            opacity: (modelData.precipitationProbability && modelData.precipitationProbability > 0) ? 0.9 : 0.4
            font.family: root.fontFamily
            font.pixelSize: Style.font.caption
          }

          Item {
            // Spacer
            width: Math.max(0, parent.width - Style.space(100 + 30 + 140 + 70) - tempRow.implicitWidth - (parent.spacing * 5))
            height: 1
          }

          // 5. High / Low Temperature
          Row {
            id: tempRow
            anchors.verticalCenter: parent.verticalCenter
            spacing: Style.space(6)

            Text {
              text: Model.bareTempForDay(modelData, "min", root.useImperial)
              color: root.foreground
              opacity: 0.55
              font.family: root.fontFamily
              font.pixelSize: Style.font.body
            }

            Text {
              text: "—"
              color: root.foreground
              opacity: 0.35
              font.family: root.fontFamily
              font.pixelSize: Style.font.body
            }

            Text {
              text: Model.bareTempForDay(modelData, "max", root.useImperial)
              color: root.foreground
              font.family: root.fontFamily
              font.pixelSize: Style.font.body
              font.bold: true
            }
          }
        }
      }
    }
  }
}
