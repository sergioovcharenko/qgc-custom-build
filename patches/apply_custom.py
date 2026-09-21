#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path.cwd()
VARIANT = sys.argv[1] if len(sys.argv) > 1 else "normal"

def read(path):
    return (ROOT/path).read_text(encoding="utf-8")

def write(path, text):
    (ROOT/path).write_text(text, encoding="utf-8")

def replace(path, old, new, count=1):
    s = read(path)
    if old not in s:
        raise SystemExit(f"Marker not found in {path}: {old[:100]!r}")
    write(path, s.replace(old, new, count))

# ---------------------------------------------------------------------------
# Stable custom baseline: keep QGC 4.4.0 as close to stock as possible.
# Add only our reticle, VISP, camera status and manual UI-only TRACK overlay.
# ---------------------------------------------------------------------------

# Custom reticle setting, matching the stable custom APK behaviour.
replace("src/Settings/FlyViewSettings.h",
'''    DEFINE_SETTINGFACT(showLogReplayStatusBar)
''',
'''    DEFINE_SETTINGFACT(showLogReplayStatusBar)
    DEFINE_SETTINGFACT(targetSize)
''')

replace("src/Settings/FlyViewSettings.cc",
'''DECLARE_SETTINGSFACT(FlyViewSettings, showLogReplayStatusBar)
''',
'''DECLARE_SETTINGSFACT(FlyViewSettings, showLogReplayStatusBar)
DECLARE_SETTINGSFACT(FlyViewSettings, targetSize)
''')

replace("src/Settings/FlyView.SettingsGroup.json",
'''{
    "name":             "showLogReplayStatusBar",''',
'''{
    "name":             "targetSize",
    "shortDesc":        "Target size",
    "type":             "string",
    "default":          "custom1",
    "enumStrings":      "None,Small,Medium,Large,Custom1",
    "enumValues":       "none,small,medium,large,custom1"
},
{
    "name":             "showLogReplayStatusBar",''')

# Main window stores TRACK UI-only state. It does not send any tracking/gimbal command.
replace("src/ui/MainRootWindow.qml",
'''    visible:        true
''',
'''    visible:        true

    property bool   customTrackUiEnabled: false
    property string customTrackPreviousTargetSize: "custom1"
''')

# ---------------------------------------------------------------------------
# VISP: use the exact source logic recovered from the stable working APK,
# but render only VISP: + coloured circle (no numeric percent).
# ---------------------------------------------------------------------------
visp = r'''import QtQuick 2.12
import QtQuick.Layouts 1.11
import QGroundControl 1.0
import QGroundControl.Controls 1.0
import QGroundControl.ScreenTools 1.0

Item {
    id: root

    property bool showIndicator: true
    property real fontSize: ScreenTools.mediumFontPointSize

    property var activeVehicle: QGroundControl.multiVehicleManager.activeVehicle
    property var engineLoadFact: activeVehicle && activeVehicle.efi ? activeVehicle.efi.engineLoad : null

    readonly property real engineLoadValue: engineLoadFact ? Number(engineLoadFact.value) : NaN
    readonly property bool hasValidValue: !isNaN(engineLoadValue)
    readonly property color vispColor: !hasValidValue ? "#808080"
                                         : (engineLoadValue < 50 ? "#ff0000"
                                         : (engineLoadValue < 96 ? "#ff9800" : "#00c853"))

    visible: activeVehicle
    implicitWidth: content.implicitWidth
    implicitHeight: parent ? parent.height : content.implicitHeight

    RowLayout {
        id: content
        anchors.fill: parent
        spacing: ScreenTools.defaultFontPixelWidth * 0.35

        QGCLabel {
            text: qsTr("VISP:")
            color: "white"
            font.pointSize: root.fontSize
            verticalAlignment: Text.AlignVCenter
        }

        Rectangle {
            width: ScreenTools.defaultFontPixelHeight * 0.58
            height: width
            radius: width / 2
            color: root.vispColor
            border.width: 1
            border.color: "white"
            Layout.alignment: Qt.AlignVCenter
        }
    }
}
'''
write("src/ui/toolbar/VISPIndicator.qml", visp)

# Add VISP QML to QRC.
s = read("qgroundcontrol.qrc")
needle = '        <file alias="TelemetryRSSIIndicator.qml">src/ui/toolbar/TelemetryRSSIIndicator.qml</file>\n'
if 'alias="VISPIndicator.qml"' not in s:
    s = s.replace(needle, needle + '        <file alias="VISPIndicator.qml">src/ui/toolbar/VISPIndicator.qml</file>\n')
write("qgroundcontrol.qrc", s)

# Put VISP directly in the toolbar before vehicle-provided indicators.
replace("src/ui/toolbar/MainToolBarIndicators.qml",
'''    Repeater {
        id:     toolIndicatorsRepeater
''',
'''    VISPIndicator {
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        visible: showIndicator
    }

    Repeater {
        id:     toolIndicatorsRepeater
''')

# ---------------------------------------------------------------------------
# TRACK button: manual green rectangle only. No camera/vehicle tracking command.
# ---------------------------------------------------------------------------
trackButton = r'''import QtQuick 2.12
import QGroundControl 1.0
import QGroundControl.Controls 1.0
import QGroundControl.ScreenTools 1.0

Rectangle {
    id: root
    property bool showIndicator: QGroundControl.multiVehicleManager.activeVehicle !== null

    implicitWidth: label.implicitWidth + ScreenTools.defaultFontPixelWidth * 1.4
    implicitHeight: parent ? parent.height : ScreenTools.defaultFontPixelHeight * 2
    radius: ScreenTools.defaultFontPixelWidth * 0.35
    color: mainWindow.customTrackUiEnabled ? "#1f7a45" : Qt.rgba(0,0,0,0.10)
    border.width: 1
    border.color: mainWindow.customTrackUiEnabled ? "#00ff66" : "white"
    visible: showIndicator

    QGCLabel {
        id: label
        anchors.centerIn: parent
        text: "TRACK"
        color: "white"
        font.family: ScreenTools.demiboldFontFamily
    }

    MouseArea {
        anchors.fill: parent
        onClicked: {
            var f = QGroundControl.settingsManager.flyViewSettings.targetSize
            if (!mainWindow.customTrackUiEnabled) {
                mainWindow.customTrackPreviousTargetSize = f.rawValue
                f.rawValue = "small"
                mainWindow.customTrackUiEnabled = true
            } else {
                mainWindow.customTrackUiEnabled = false
                f.rawValue = mainWindow.customTrackPreviousTargetSize
            }
        }
    }
}
'''
write("src/ui/toolbar/TrackIndicator.qml", trackButton)

s = read("qgroundcontrol.qrc")
needle = '        <file alias="VISPIndicator.qml">src/ui/toolbar/VISPIndicator.qml</file>\n'
if 'alias="TrackIndicator.qml"' not in s:
    s = s.replace(needle, needle + '        <file alias="TrackIndicator.qml">src/ui/toolbar/TrackIndicator.qml</file>\n')
write("qgroundcontrol.qrc", s)

replace("src/ui/toolbar/MainToolBarIndicators.qml",
'''    VISPIndicator {
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        visible: showIndicator
    }
''',
'''    VISPIndicator {
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        visible: showIndicator
    }

    TrackIndicator {
        anchors.verticalCenter: parent.verticalCenter
        visible: showIndicator
    }
''')

# ---------------------------------------------------------------------------
# Reticle and camera angle/zoom. Kept inside the video view so they do not
# affect the rest of QGC.
# ---------------------------------------------------------------------------
fdv = ROOT/"src/FlightDisplay/FlightDisplayViewVideo.qml"
s = fdv.read_text(encoding="utf-8")
insert = r'''

    Canvas {
        id: customReticle
        anchors.fill: parent
        z: 900
        visible: QGroundControl.settingsManager.flyViewSettings.targetSize.rawValue !== "none"
        property string targetSize: QGroundControl.settingsManager.flyViewSettings.targetSize.rawValue

        onTargetSizeChanged: requestPaint()
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            var cx = width / 2
            var cy = height / 2
            var radius = 30
            var extent = 0
            var ticks = 0
            if (targetSize === "small") { extent = 150; ticks = 8 }
            else if (targetSize === "medium") { extent = 240; ticks = 12 }
            else if (targetSize === "large") { extent = 480; ticks = 20 }
            else if (targetSize === "custom1") { extent = 360; ticks = 16 }

            ctx.lineWidth = 2
            ctx.strokeStyle = "red"
            ctx.fillStyle = "red"

            ctx.beginPath()
            ctx.arc(cx, cy, radius, 0, Math.PI * 2)
            ctx.stroke()

            ctx.beginPath()
            ctx.arc(cx, cy, 2.2, 0, Math.PI * 2)
            ctx.fill()

            var stick = 8
            ctx.beginPath()
            ctx.moveTo(cx, cy-radius/2); ctx.lineTo(cx, cy-radius-stick)
            ctx.moveTo(cx, cy+radius/2); ctx.lineTo(cx, cy+radius+stick)
            ctx.moveTo(cx-radius/2, cy); ctx.lineTo(cx-radius-stick, cy)
            ctx.moveTo(cx+radius/2, cy); ctx.lineTo(cx+radius+stick, cy)
            ctx.stroke()

            if (ticks > 0) {
                var step = (extent - radius) / (ticks + 1)
                for (var i=0; i<ticks; i++) {
                    var sz = (i % 2 === 0) ? 12 : 20
                    var o = radius + step + i * step
                    ctx.beginPath()
                    ctx.moveTo(cx-sz/2, cy-o); ctx.lineTo(cx+sz/2, cy-o)
                    ctx.moveTo(cx-sz/2, cy+o); ctx.lineTo(cx+sz/2, cy+o)
                    ctx.moveTo(cx-o, cy-sz/2); ctx.lineTo(cx-o, cy+sz/2)
                    ctx.moveTo(cx+o, cy-sz/2); ctx.lineTo(cx+o, cy+sz/2)
                    ctx.stroke()
                }
            }

            if (targetSize === "custom1") {
                var d = 92
                var e = 54
                ctx.beginPath()
                ctx.moveTo(cx-d,cy-e); ctx.lineTo(cx-e,cy-d)
                ctx.moveTo(cx+d,cy-e); ctx.lineTo(cx+e,cy-d)
                ctx.moveTo(cx-d,cy+e); ctx.lineTo(cx-e,cy+d)
                ctx.moveTo(cx+d,cy+e); ctx.lineTo(cx+e,cy+d)
                ctx.stroke()
            }
        }
    }

    property var _customVehicle: QGroundControl.multiVehicleManager.activeVehicle
    property var _customGimbal: _customVehicle && _customVehicle.gimbalController ? _customVehicle.gimbalController.activeGimbal : null

    Column {
        z: 950
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.rightMargin: ScreenTools.defaultFontPixelWidth * 2
        anchors.bottomMargin: ScreenTools.defaultFontPixelHeight * 1.4
        spacing: ScreenTools.defaultFontPixelHeight * 0.15

        QGCLabel {
            anchors.right: parent.right
            text: _customGimbal && _customGimbal.absolutePitch
                  ? ("∠ " + Math.round(Number(_customGimbal.absolutePitch.rawValue)) + "°")
                  : "∠ --°"
            color: "white"
            font.family: ScreenTools.demiboldFontFamily
            font.pointSize: ScreenTools.mediumFontPointSize
        }

        QGCLabel {
            anchors.right: parent.right
            text: _camera && !isNaN(Number(_camera.zoomLevel))
                  ? ("x" + Math.round(Number(_camera.zoomLevel)))
                  : "x--"
            color: "white"
            font.family: ScreenTools.demiboldFontFamily
            font.pointSize: ScreenTools.mediumFontPointSize
        }
    }
'''
i = s.rfind("}")
if i < 0:
    raise SystemExit("No closing brace in FlightDisplayViewVideo.qml")
s = s[:i] + insert + "\n" + s[i:]
fdv.write_text(s, encoding="utf-8")

# ---------------------------------------------------------------------------
# Manual TRACK overlay.
# ---------------------------------------------------------------------------
fly = ROOT/"src/FlightDisplay/FlyViewVideo.qml"
s = fly.read_text(encoding="utf-8")
insert = r'''

    property bool _customTrackAreaCreated: false

    Connections {
        target: mainWindow
        function onCustomTrackUiEnabledChanged() {
            if (!mainWindow.customTrackUiEnabled) {
                _customTrackAreaCreated = false
            }
        }
    }

    Rectangle {
        z: 1990
        visible: mainWindow.customTrackUiEnabled && !_customTrackAreaCreated
        anchors.top: parent.top
        anchors.topMargin: ScreenTools.defaultFontPixelHeight * 0.8
        anchors.horizontalCenter: parent.horizontalCenter
        width: hintText.implicitWidth + ScreenTools.defaultFontPixelWidth * 3
        height: hintText.implicitHeight + ScreenTools.defaultFontPixelHeight
        radius: ScreenTools.defaultFontPixelWidth * 0.5
        color: Qt.rgba(0,0,0,0.72)

        QGCLabel {
            id: hintText
            anchors.centerIn: parent
            text: qsTr("Виберіть зону супроводження")
            color: "white"
            font.family: ScreenTools.demiboldFontFamily
        }
    }

    MouseArea {
        z: 1980
        anchors.fill: parent
        enabled: mainWindow.customTrackUiEnabled && !_customTrackAreaCreated

        onClicked: {
            customTrackRect.width = Math.min(220, parent.width * 0.28)
            customTrackRect.height = Math.min(160, parent.height * 0.25)
            customTrackRect.x = Math.max(0, Math.min(mouse.x - customTrackRect.width/2, parent.width-customTrackRect.width))
            customTrackRect.y = Math.max(0, Math.min(mouse.y - customTrackRect.height/2, parent.height-customTrackRect.height))
            _customTrackAreaCreated = true
        }
    }

    Rectangle {
        id: customTrackRect
        z: 2000
        visible: mainWindow.customTrackUiEnabled && _customTrackAreaCreated
        width: 220
        height: 160
        color: "transparent"
        border.color: "#00ff66"
        border.width: 3
        radius: 2

        MouseArea {
            anchors.fill: parent
            anchors.margins: 18
            drag.target: customTrackRect
            drag.minimumX: 0
            drag.minimumY: 0
            drag.maximumX: customTrackRect.parent.width - customTrackRect.width
            drag.maximumY: customTrackRect.parent.height - customTrackRect.height
        }

        Rectangle {
            width: 28
            height: 28
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            color: "#00ff66"
            radius: 4

            MouseArea {
                anchors.fill: parent
                property real px
                property real py
                property real pw
                property real ph

                onPressed: {
                    px = mouse.x
                    py = mouse.y
                    pw = customTrackRect.width
                    ph = customTrackRect.height
                }

                onPositionChanged: if (pressed) {
                    customTrackRect.width = Math.max(80, Math.min(customTrackRect.parent.width-customTrackRect.x, pw + mouse.x-px))
                    customTrackRect.height = Math.max(80, Math.min(customTrackRect.parent.height-customTrackRect.y, ph + mouse.y-py))
                }
            }
        }
    }
'''
i = s.rfind("}")
if i < 0:
    raise SystemExit("No closing brace in FlyViewVideo.qml")
s = s[:i] + insert + "\n" + s[i:]
fly.write_text(s, encoding="utf-8")

print("Stable-minimal custom patch applied:", VARIANT)
