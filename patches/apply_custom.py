#!/usr/bin/env python3
from pathlib import Path
import base64, sys

ROOT = Path.cwd()
VARIANT = sys.argv[1] if len(sys.argv) > 1 else 'normal'

def edit(path, old, new, count=1):
    p=ROOT/path
    s=p.read_text(encoding='utf-8')
    if old not in s:
        raise SystemExit(f'Marker not found in {path}: {old[:80]!r}')
    s=s.replace(old,new,count)
    p.write_text(s,encoding='utf-8')

def append_before_last(path, content):
    p=ROOT/path
    s=p.read_text(encoding='utf-8')
    i=s.rfind('}')
    if i<0: raise SystemExit(f'No closing brace in {path}')
    p.write_text(s[:i]+content+'\n'+s[i:],encoding='utf-8')

edit('src/ui/MainRootWindow.qml',
'''    visible:        true\n''',
'''    visible:        true\n\n    // Custom UI-only TRACK selection state (does not command the vehicle/camera)\n    property bool   customTrackUiEnabled: false\n    property string customTrackPreviousTargetSize: "medium"\n''')

edit('src/Settings/FlyViewSettings.h',
'''    DEFINE_SETTINGFACT(showLogReplayStatusBar)\n''',
'''    DEFINE_SETTINGFACT(showLogReplayStatusBar)\n    DEFINE_SETTINGFACT(targetSize)\n''')
edit('src/Settings/FlyViewSettings.cc',
'''DECLARE_SETTINGSFACT(FlyViewSettings, showLogReplayStatusBar)\n''',
'''DECLARE_SETTINGSFACT(FlyViewSettings, showLogReplayStatusBar)\nDECLARE_SETTINGSFACT(FlyViewSettings, targetSize)\n''')
edit('src/Settings/FlyView.SettingsGroup.json',
'''{\n    "name":             "showLogReplayStatusBar",''',
'''{\n    "name":             "targetSize",\n    "shortDesc":        "Target size",\n    "type":             "string",\n    "default":          "medium",\n    "enumStrings":      "None,Small,Medium,Large,Custom1",\n    "enumValues":       "none,small,medium,large,custom1"\n},\n{\n    "name":             "showLogReplayStatusBar",''')

edit('src/ui/preferences/GeneralSettings.qml',
'''                            FactCheckBox {\n                                text:       qsTr("Show Telemetry Log Replay Status Bar")\n                                fact:       _showLogReplayStatusBar\n                                visible:    _showLogReplayStatusBar.visible\n\n                                property Fact _showLogReplayStatusBar: QGroundControl.settingsManager.flyViewSettings.showLogReplayStatusBar\n                            }\n''',
'''                            FactCheckBox {\n                                text:       qsTr("Show Telemetry Log Replay Status Bar")\n                                fact:       _showLogReplayStatusBar\n                                visible:    _showLogReplayStatusBar.visible\n\n                                property Fact _showLogReplayStatusBar: QGroundControl.settingsManager.flyViewSettings.showLogReplayStatusBar\n                            }\n\n                            RowLayout {\n                                QGCLabel { text: qsTr("Target size") }\n                                FactComboBox {\n                                    fact: QGroundControl.settingsManager.flyViewSettings.targetSize\n                                    Layout.preferredWidth: ScreenTools.defaultFontPixelWidth * 18\n                                }\n                            }\n''')

rcrssi = r'''/****************************************************************************
 * Custom RC RSSI indicator
 ****************************************************************************/
import QtQuick 2.11
import QtQuick.Layouts 1.11
import QGroundControl 1.0
import QGroundControl.Controls 1.0
import QGroundControl.MultiVehicleManager 1.0
import QGroundControl.ScreenTools 1.0
import QGroundControl.Palette 1.0

Item {
    id: _root
    anchors.top: parent.top
    anchors.bottom: parent.bottom
    width: rssiRow.width * 1.05
    property var _activeVehicle: QGroundControl.multiVehicleManager.activeVehicle
    property bool _rcRSSIAvailable: _activeVehicle ? _activeVehicle.rcRSSI > 0 && _activeVehicle.rcRSSI <= 100 : false
    property bool showIndicator: _activeVehicle && _activeVehicle.supportsRadio && _rcRSSIAvailable

    Row {
        id: rssiRow
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        spacing: ScreenTools.defaultFontPixelWidth * 0.45
        QGCColoredImage {
            width: height
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            sourceSize.height: height
            source: "/qmlimages/RC.svg"
            fillMode: Image.PreserveAspectFit
            opacity: _rcRSSIAvailable ? 1 : 0.5
            color: _rcRSSIAvailable && _activeVehicle.rcRSSI <= 45 ? "red" : qgcPal.buttonText
        }
        QGCLabel {
            anchors.verticalCenter: parent.verticalCenter
            text: _rcRSSIAvailable ? (_activeVehicle.rcRSSI + "%") : "--"
            color: _rcRSSIAvailable && _activeVehicle.rcRSSI <= 45 ? "red" : qgcPal.buttonText
            font.family: ScreenTools.demiboldFontFamily
        }
    }
}
'''
(ROOT/'src/ui/toolbar/RCRSSIIndicator.qml').write_text(rcrssi,encoding='utf-8')


status_dot = r'''import QtQuick 2.11
import QGroundControl.ScreenTools 1.0

Rectangle {
    id: root
    property color statusColor: "#808080"
    property real dotScale: 0.60

    width: ScreenTools.defaultFontPixelHeight * dotScale
    height: width
    radius: width / 2
    color: statusColor
    border.width: 1
    border.color: Qt.rgba(1,1,1,0.75)
}
'''
(ROOT/'src/ui/toolbar/StatusDot.qml').write_text(status_dot, encoding='utf-8')

visp_indicator = r'''import QtQuick 2.11
import QtQuick.Layouts 1.11
import QGroundControl 1.0
import QGroundControl.Controls 1.0
import QGroundControl.ScreenTools 1.0

Item {
    id: root

    property real value: NaN
    property color noDataColor: "#808080"
    property color badColor: "#ff0000"
    property color warningColor: "#ff9800"
    property color goodColor: "#00c853"

    readonly property color stateColor: isNaN(value)
                                        ? noDataColor
                                        : (value < 50
                                           ? badColor
                                           : (value < 96 ? warningColor : goodColor))

    implicitWidth: row.implicitWidth
    implicitHeight: row.implicitHeight

    Row {
        id: row
        anchors.verticalCenter: parent.verticalCenter
        spacing: ScreenTools.defaultFontPixelWidth * 0.35

        QGCLabel {
            anchors.verticalCenter: parent.verticalCenter
            text: "VISP:"
            color: "white"
            font.family: ScreenTools.demiboldFontFamily
        }

        StatusDot {
            anchors.verticalCenter: parent.verticalCenter
            statusColor: root.stateColor
        }
    }
}
'''
(ROOT/'src/ui/toolbar/VISPIndicator.qml').write_text(visp_indicator, encoding='utf-8')

# Make the two new QML files available through the same /qml resource prefix.
qrc = ROOT/'qgroundcontrol.qrc'
qs = qrc.read_text(encoding='utf-8')
needle = '        <file alias="TelemetryRSSIIndicator.qml">src/ui/toolbar/TelemetryRSSIIndicator.qml</file>\n'
replacement = needle + '        <file alias="StatusDot.qml">src/ui/toolbar/StatusDot.qml</file>\n' + '        <file alias="VISPIndicator.qml">src/ui/toolbar/VISPIndicator.qml</file>\n'
if 'alias="VISPIndicator.qml"' not in qs:
    qs = qs.replace(needle, replacement)
qrc.write_text(qs, encoding='utf-8')

telem = r'''/****************************************************************************
 * Custom telemetry / VISP / TRACK toolbar indicator
 ****************************************************************************/
import QtQuick 2.11
import QtQuick.Layouts 1.11
import QGroundControl 1.0
import QGroundControl.Controls 1.0
import QGroundControl.MultiVehicleManager 1.0
import QGroundControl.ScreenTools 1.0
import QGroundControl.Palette 1.0

Item {
    id: _root
    anchors.top: parent.top
    anchors.bottom: parent.bottom
    width: row.width
    property bool showIndicator: _activeVehicle !== null
    property var _activeVehicle: QGroundControl.multiVehicleManager.activeVehicle
    property bool _commLost: _activeVehicle && _activeVehicle.vehicleLinkManager ? _activeVehicle.vehicleLinkManager.communicationLost : false
    property real _lrssi: _activeVehicle ? Number(_activeVehicle.telemetryLRSSI) : NaN
    property real _rrssi: _activeVehicle ? Number(_activeVehicle.telemetryRRSSI) : NaN
    property bool _hasL: !isNaN(_lrssi) && _lrssi !== 0
    property bool _hasR: !isNaN(_rrssi) && _rrssi !== 0
    property bool _hasTelemetry: _activeVehicle && !_commLost && (_hasL || _hasR)
    // -128 dBm is a valid weak-signal value. It does NOT mean telemetry is lost.
    property real _dbm: !_hasTelemetry ? NaN : (_hasL && _hasR ? Math.max(_lrssi, _rrssi) : (_hasL ? _lrssi : _rrssi))
    property real _visp: (_activeVehicle && _activeVehicle.efi && _activeVehicle.efi.engineLoad) ? Number(_activeVehicle.efi.engineLoad.rawValue) : NaN
    property color _vispColor: isNaN(_visp) ? "#808080" : (_visp < 50 ? "#ff0000" : (_visp < 96 ? "#ff9800" : "#00c853"))

    Row {
        id: row
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        spacing: ScreenTools.defaultFontPixelWidth * 0.55
        QGCColoredImage {
            width: height
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            sourceSize.height: height
            source: "/qmlimages/TelemRSSI.svg"
            fillMode: Image.PreserveAspectFit
            color: qgcPal.buttonText
        }
        QGCLabel {
            anchors.verticalCenter: parent.verticalCenter
            text: _hasTelemetry ? (Math.round(_dbm) + " dBm") : "-- dBm"
            color: qgcPal.buttonText
            font.family: ScreenTools.demiboldFontFamily
        }
        VISPIndicator {
            anchors.verticalCenter: parent.verticalCenter
            value: _visp
        }
        Rectangle {
            id: trackButton
            anchors.verticalCenter: parent.verticalCenter
            height: parent.height * 0.72
            width: trackText.implicitWidth + ScreenTools.defaultFontPixelWidth * 1.3
            radius: ScreenTools.defaultFontPixelWidth * 0.35
            color: mainWindow.customTrackUiEnabled ? "#1f7a45" : Qt.rgba(0,0,0,0.15)
            border.width: 1
            border.color: mainWindow.customTrackUiEnabled ? "#00ff66" : qgcPal.buttonText
            QGCLabel {
                id: trackText
                anchors.centerIn: parent
                text: "TRACK"
                color: mainWindow.customTrackUiEnabled ? "white" : qgcPal.buttonText
                font.family: ScreenTools.demiboldFontFamily
            }
            MouseArea {
                anchors.fill: parent
                onClicked: {
                    var fact = QGroundControl.settingsManager.flyViewSettings.targetSize
                    if (!mainWindow.customTrackUiEnabled) {
                        mainWindow.customTrackPreviousTargetSize = fact.rawValue
                        fact.rawValue = "small"
                        mainWindow.customTrackUiEnabled = true
                    } else {
                        mainWindow.customTrackUiEnabled = false
                        fact.rawValue = mainWindow.customTrackPreviousTargetSize
                    }
                }
            }
        }
    }
}
'''
(ROOT/'src/ui/toolbar/TelemetryRSSIIndicator.qml').write_text(telem,encoding='utf-8')

fdv = ROOT/'src/FlightDisplay/FlightDisplayViewVideo.qml'
s = fdv.read_text(encoding='utf-8')
insert = r'''

    // Video weak-signal overlay with hysteresis. Telemetry remains independent.
    property var _customVehicle: QGroundControl.multiVehicleManager.activeVehicle
    property real _customLrssi: _customVehicle ? Number(_customVehicle.telemetryLRSSI) : NaN
    property real _customRrssi: _customVehicle ? Number(_customVehicle.telemetryRRSSI) : NaN
    property real _customDbm: (!isNaN(_customLrssi) && _customLrssi !== 0 && !isNaN(_customRrssi) && _customRrssi !== 0) ? Math.max(_customLrssi,_customRrssi) : ((!isNaN(_customLrssi) && _customLrssi !== 0) ? _customLrssi : _customRrssi)
    property bool _customWeakVideo: false
    on_CustomDbmChanged: {
        if (!isNaN(_customDbm)) {
            if (_customDbm <= -90) _customWeakVideo = true
            else if (_customDbm > -85 && QGroundControl.videoManager.decoding) _customWeakVideo = false
        }
    }
    Image {
        z: 850
        anchors.fill: parent
        visible: _customWeakVideo || !QGroundControl.videoManager.decoding
        source: "/res/NoVideoBackground.jpg"
        fillMode: Image.PreserveAspectCrop
    }

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
            var cx = width/2, cy = height/2
            var radius = 30
            var arrowLength = 0, count = 0
            if (targetSize === "medium") { arrowLength = 240; count = 12 }
            else if (targetSize === "large") { arrowLength = 480; count = 20 }
            else if (targetSize === "custom1") { arrowLength = 360; count = 16 }
            ctx.lineWidth = 2
            ctx.strokeStyle = "red"
            ctx.fillStyle = "red"
            ctx.beginPath(); ctx.arc(cx,cy,radius,0,Math.PI*2); ctx.stroke()
            ctx.beginPath(); ctx.arc(cx,cy,2,0,Math.PI*2); ctx.fill()
            var stick=8
            ctx.beginPath()
            ctx.moveTo(cx,cy-radius/2); ctx.lineTo(cx,cy-radius-stick)
            ctx.moveTo(cx,cy+radius/2); ctx.lineTo(cx,cy+radius+stick)
            ctx.moveTo(cx-radius/2,cy); ctx.lineTo(cx-radius-stick,cy)
            ctx.moveTo(cx+radius/2,cy); ctx.lineTo(cx+radius+stick,cy)
            ctx.stroke()
            if (count>0) {
                var spacing=(arrowLength-radius)/(count+1)
                for(var i=0;i<count;i++) {
                    var size=(i%2===0)?12:20
                    var o=radius+spacing+i*spacing
                    ctx.beginPath()
                    ctx.moveTo(cx-size/2,cy-o); ctx.lineTo(cx+size/2,cy-o)
                    ctx.moveTo(cx-size/2,cy+o); ctx.lineTo(cx+size/2,cy+o)
                    ctx.moveTo(cx-o,cy-size/2); ctx.lineTo(cx-o,cy+size/2)
                    ctx.moveTo(cx+o,cy-size/2); ctx.lineTo(cx+o,cy+size/2)
                    ctx.stroke()
                }
            }
            if (targetSize === "custom1") {
                var d=92, e=54
                ctx.beginPath()
                ctx.moveTo(cx-d,cy-e); ctx.lineTo(cx-e,cy-d)
                ctx.moveTo(cx+d,cy-e); ctx.lineTo(cx+e,cy-d)
                ctx.moveTo(cx-d,cy+e); ctx.lineTo(cx-e,cy+d)
                ctx.moveTo(cx+d,cy+e); ctx.lineTo(cx+e,cy+d)
                ctx.stroke()
            }
        }
    }

    property var _customActiveGimbal: globals.activeVehicle && globals.activeVehicle.gimbalController ? globals.activeVehicle.gimbalController.activeGimbal : null
    Column {
        z: 950
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.rightMargin: ScreenTools.defaultFontPixelWidth * 2
        anchors.bottomMargin: ScreenTools.defaultFontPixelHeight * 1.5
        spacing: ScreenTools.defaultFontPixelHeight * 0.15
        QGCLabel {
            anchors.right: parent.right
            text: _customActiveGimbal && _customActiveGimbal.absolutePitch ? ("∠ " + Math.round(Number(_customActiveGimbal.absolutePitch.rawValue)) + "°") : "∠ --°"
            color: "white"
            font.family: ScreenTools.demiboldFontFamily
            font.pointSize: ScreenTools.mediumFontPointSize
        }
        QGCLabel {
            anchors.right: parent.right
            text: _camera && !isNaN(Number(_camera.zoomLevel)) ? ("x" + Math.round(Number(_camera.zoomLevel))) : "x--"
            color: "white"
            font.family: ScreenTools.demiboldFontFamily
            font.pointSize: ScreenTools.mediumFontPointSize
        }
    }
'''
i=s.rfind('}')
s=s[:i]+insert+'\n'+s[i:]
fdv.write_text(s,encoding='utf-8')

fly = ROOT/'src/FlightDisplay/FlyViewVideo.qml'
s=fly.read_text(encoding='utf-8')
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
        id: customTrackHint
        z: 1990
        visible: mainWindow.customTrackUiEnabled && !_customTrackAreaCreated
        anchors.top: parent.top
        anchors.topMargin: ScreenTools.defaultFontPixelHeight * 0.8
        anchors.horizontalCenter: parent.horizontalCenter
        width: customTrackHintText.implicitWidth + ScreenTools.defaultFontPixelWidth * 3
        height: customTrackHintText.implicitHeight + ScreenTools.defaultFontPixelHeight
        radius: ScreenTools.defaultFontPixelWidth * 0.5
        color: Qt.rgba(0,0,0,0.70)
        QGCLabel {
            id: customTrackHintText
            anchors.centerIn: parent
            text: qsTr("Виберіть зону супроводження")
            color: "white"
            font.family: ScreenTools.demiboldFontFamily
        }
    }

    MouseArea {
        id: customTrackCreateArea
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
            id: customTrackDrag
            anchors.fill: parent
            anchors.margins: 18
            drag.target: customTrackRect
            drag.minimumX: 0
            drag.minimumY: 0
            drag.maximumX: customTrackRect.parent.width - customTrackRect.width
            drag.maximumY: customTrackRect.parent.height - customTrackRect.height
        }

        Rectangle {
            id: customResizeHandle
            width: 28; height: 28
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
                onPressed: { px=mouse.x; py=mouse.y; pw=customTrackRect.width; ph=customTrackRect.height }
                onPositionChanged: if (pressed) {
                    customTrackRect.width = Math.max(80, Math.min(customTrackRect.parent.width-customTrackRect.x, pw + mouse.x-px))
                    customTrackRect.height = Math.max(80, Math.min(customTrackRect.parent.height-customTrackRect.y, ph + mouse.y-py))
                }
            }
        }
    }
'''
i=s.rfind('}')
s=s[:i]+insert+'\n'+s[i:]
fly.write_text(s,encoding='utf-8')

if VARIANT.lower() == 'active10':
    p=ROOT/'src/Settings/Video.SettingsGroup.json'
    s=p.read_text(encoding='utf-8')
    marker='''    "name":             "forceVideoDecoder",'''
    idx=s.find(marker)
    if idx>=0:
        end=s.find('}',idx)
        block=s[idx:end]
        block2=block.replace('"default":           0','"default":           1')
        s=s[:idx]+block2+s[end:]
        p.write_text(s,encoding='utf-8')

print('Custom QGC patches applied for', VARIANT)


# Active 10 Pro / custom Fly View: keep video as the main surface even before a live
# stream is detected, so the custom no-video background is visible instead of the map.
flyview = ROOT/'src/FlightDisplay/FlyView.qml'
s = flyview.read_text(encoding='utf-8')
s = s.replace('item1IsFullSettingsKey: "MainFlyWindowIsMap"', 'item1IsFullSettingsKey: "MainFlyWindowIsVideoCustom"')
s = s.replace('item1:                  mapControl\n        item2:                  QGroundControl.videoManager.hasVideo ? videoControl : null',
              'item1:                  videoControl\n        item2:                  mapControl')
flyview.write_text(s, encoding='utf-8')

flyvideo = ROOT/'src/FlightDisplay/FlyViewVideo.qml'
s = flyvideo.read_text(encoding='utf-8')
s = s.replace('visible:    QGroundControl.videoManager.hasVideo', 'visible:    true', 1)
flyvideo.write_text(s, encoding='utf-8')

# The custom MONOLIT image itself is injected into the built APK/resource bundle;
# keep the no-video screen clean without the stock WAITING FOR VIDEO label.
fdv = ROOT/'src/FlightDisplay/FlightDisplayViewVideo.qml'
s = fdv.read_text(encoding='utf-8')
s = s.replace('text:               QGroundControl.settingsManager.videoSettings.streamEnabled.rawValue ? qsTr("WAITING FOR VIDEO") : qsTr("VIDEO DISABLED")',
              'text:               ""')
fdv.write_text(s, encoding='utf-8')
