#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()

def read(path):
    return (ROOT/path).read_text(encoding="utf-8")

def write(path, text):
    (ROOT/path).write_text(text, encoding="utf-8")

# X-Target + selectable colour.
s = read("src/Settings/FlyViewSettings.h")
if "DEFINE_SETTINGFACT(targetColor)" not in s:
    s = s.replace("    DEFINE_SETTINGFACT(targetSize)\n",
                  "    DEFINE_SETTINGFACT(targetSize)\n    DEFINE_SETTINGFACT(targetColor)\n", 1)
write("src/Settings/FlyViewSettings.h", s)

s = read("src/Settings/FlyViewSettings.cc")
if "DECLARE_SETTINGSFACT(FlyViewSettings, targetColor)" not in s:
    s = s.replace("DECLARE_SETTINGSFACT(FlyViewSettings, targetSize)\n",
                  "DECLARE_SETTINGSFACT(FlyViewSettings, targetSize)\nDECLARE_SETTINGSFACT(FlyViewSettings, targetColor)\n", 1)
write("src/Settings/FlyViewSettings.cc", s)

s = read("src/Settings/FlyView.SettingsGroup.json")
old_target = '''{
    "name":             "targetSize",
    "shortDesc":        "Target size",
    "type":             "string",
    "default":          "custom1",
    "enumStrings":      "None,Small,Medium,Large,Custom1",
    "enumValues":       "none,small,medium,large,custom1"
},'''
new_target = '''{
    "name":             "targetSize",
    "shortDesc":        "Target size",
    "type":             "string",
    "default":          "x-target",
    "enumStrings":      "None,Small,Medium,Large,X-Target",
    "enumValues":       "none,small,medium,large,x-target"
},
{
    "name":             "targetColor",
    "shortDesc":        "Target color",
    "type":             "string",
    "default":          "red",
    "enumStrings":      "Red,Green,White,Yellow,Cyan",
    "enumValues":       "red,green,white,yellow,cyan"
},'''
if old_target in s:
    s = s.replace(old_target, new_target, 1)
elif '"name":             "targetColor"' not in s:
    raise SystemExit("Could not update target settings metadata")
write("src/Settings/FlyView.SettingsGroup.json", s)

# Runtime state. Dehaze starts OFF after each app launch.
s = read("src/ui/MainRootWindow.qml")
s = s.replace('property string customTrackPreviousTargetSize: "custom1"',
              'property string customTrackPreviousTargetSize: "x-target"')
if "property string customDehazeMode" not in s:
    s = s.replace('    property string customTrackPreviousTargetSize: "x-target"\n',
                  '    property string customTrackPreviousTargetSize: "x-target"\n'
                  '    property string customDehazeMode: "off"\n', 1)
write("src/ui/MainRootWindow.qml", s)

# Reticle implementation.
p = "src/FlightDisplay/FlightDisplayViewVideo.qml"
s = read(p)
s = s.replace('"custom1"', '"x-target"')
if "property string targetColor:" not in s:
    s = s.replace(
'''        property string targetSize: QGroundControl.settingsManager.flyViewSettings.targetSize.rawValue

        onTargetSizeChanged: requestPaint()
''',
'''        property string targetSize: QGroundControl.settingsManager.flyViewSettings.targetSize.rawValue
        property string targetColor: QGroundControl.settingsManager.flyViewSettings.targetColor.rawValue

        onTargetSizeChanged: requestPaint()
        onTargetColorChanged: requestPaint()
''', 1)
s = s.replace(
'''            ctx.lineWidth = 2
            ctx.strokeStyle = "red"
            ctx.fillStyle = "red"
''',
'''            var reticleColor = targetColor === "green" ? "#00ff00"
                             : targetColor === "white" ? "#ffffff"
                             : targetColor === "yellow" ? "#ffff00"
                             : targetColor === "cyan" ? "#00e5ff"
                             : "#ff0000"
            ctx.lineWidth = 2
            ctx.strokeStyle = reticleColor
            ctx.fillStyle = reticleColor
''', 1)
s = s.replace(
'''            if (targetSize === "x-target") {
                var d = 92
                var e = 54
                ctx.beginPath()
                ctx.moveTo(cx-d,cy-e); ctx.lineTo(cx-e,cy-d)
                ctx.moveTo(cx+d,cy-e); ctx.lineTo(cx+e,cy-d)
                ctx.moveTo(cx-d,cy+e); ctx.lineTo(cx-e,cy+d)
                ctx.moveTo(cx+d,cy+e); ctx.lineTo(cx+e,cy+d)
                ctx.stroke()
            }
''',
'''            if (targetSize === "x-target") {
                var d = 92
                var e = 54
                ctx.beginPath()
                ctx.moveTo(cx-d,cy-e); ctx.lineTo(cx-e,cy-d)
                ctx.moveTo(cx+d,cy-e); ctx.lineTo(cx+e,cy-d)
                ctx.moveTo(cx-d,cy+e); ctx.lineTo(cx-e,cy+d)
                ctx.moveTo(cx+d,cy+e); ctx.lineTo(cx+e,cy+d)
                ctx.stroke()
                ctx.lineWidth = 3
                ctx.beginPath()
                ctx.moveTo(cx-7, cy-7); ctx.lineTo(cx+7, cy+7)
                ctx.moveTo(cx+7, cy-7); ctx.lineTo(cx-7, cy+7)
                ctx.stroke()
            }
''', 1)
write(p, s)

# Digital Dehazing menu attached directly to the RC RSSI indicator.
p = "src/ui/toolbar/RCRSSIIndicator.qml"
s = read(p)
if "id: digitalDehazeInfo" not in s:
    marker = '''    Row {
        id:             rssiRow
'''
    menu = r'''    Component {
        id: digitalDehazeInfo

        Rectangle {
            width:  ScreenTools.defaultFontPixelWidth * 32
            height: dehazeMenuColumn.height + ScreenTools.defaultFontPixelHeight * 2
            radius: ScreenTools.defaultFontPixelHeight * 0.5
            color:  qgcPal.window
            border.color: qgcPal.text

            Column {
                id: dehazeMenuColumn
                anchors.centerIn: parent
                spacing: ScreenTools.defaultFontPixelHeight * 0.45

                QGCLabel {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: qsTr("DIGITAL DEHAZING")
                    color: "white"
                    font.family: ScreenTools.demiboldFontFamily
                }

                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: ScreenTools.defaultFontPixelWidth

                    Repeater {
                        model: [
                            { "label": "OFF",  "mode": "off" },
                            { "label": "AUTO", "mode": "auto" }
                        ]

                        Rectangle {
                            width: ScreenTools.defaultFontPixelWidth * 8
                            height: ScreenTools.defaultFontPixelHeight * 2
                            radius: ScreenTools.defaultFontPixelWidth * 0.35
                            color: mainWindow.customDehazeMode === modelData.mode ? "#1f7a45" : qgcPal.button
                            border.width: 1
                            border.color: mainWindow.customDehazeMode === modelData.mode ? "#00ff66" : qgcPal.text

                            QGCLabel {
                                anchors.centerIn: parent
                                text: modelData.label
                                color: "white"
                                font.family: ScreenTools.demiboldFontFamily
                            }

                            MouseArea {
                                anchors.fill: parent
                                onClicked: mainWindow.customDehazeMode = modelData.mode
                            }
                        }
                    }
                }

                QGCLabel {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: qsTr("MANUAL")
                    color: "white"
                    font.family: ScreenTools.demiboldFontFamily
                }

                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: ScreenTools.defaultFontPixelWidth * 0.6

                    Repeater {
                        model: [
                            { "label": "LOW",    "mode": "low" },
                            { "label": "MEDIUM", "mode": "medium" },
                            { "label": "HIGH",   "mode": "high" }
                        ]

                        Rectangle {
                            width: ScreenTools.defaultFontPixelWidth * 8
                            height: ScreenTools.defaultFontPixelHeight * 2
                            radius: ScreenTools.defaultFontPixelWidth * 0.35
                            color: mainWindow.customDehazeMode === modelData.mode ? "#1f7a45" : qgcPal.button
                            border.width: 1
                            border.color: mainWindow.customDehazeMode === modelData.mode ? "#00ff66" : qgcPal.text

                            QGCLabel {
                                anchors.centerIn: parent
                                text: modelData.label
                                color: "white"
                                font.pointSize: ScreenTools.smallFontPointSize
                                font.family: ScreenTools.demiboldFontFamily
                            }

                            MouseArea {
                                anchors.fill: parent
                                onClicked: mainWindow.customDehazeMode = modelData.mode
                            }
                        }
                    }
                }

                QGCLabel {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: qsTr("RETICLE COLOR")
                    color: "white"
                    font.family: ScreenTools.demiboldFontFamily
                }

                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: ScreenTools.defaultFontPixelWidth * 0.8

                    Repeater {
                        model: [
                            { "value": "red",    "colorValue": "#ff0000" },
                            { "value": "green",  "colorValue": "#00ff00" },
                            { "value": "white",  "colorValue": "#ffffff" },
                            { "value": "yellow", "colorValue": "#ffff00" },
                            { "value": "cyan",   "colorValue": "#00e5ff" }
                        ]

                        Rectangle {
                            width: ScreenTools.defaultFontPixelHeight * 1.45
                            height: width
                            radius: width / 2
                            color: modelData.colorValue
                            border.width: QGroundControl.settingsManager.flyViewSettings.targetColor.rawValue === modelData.value ? 3 : 1
                            border.color: "white"

                            MouseArea {
                                anchors.fill: parent
                                onClicked: QGroundControl.settingsManager.flyViewSettings.targetColor.rawValue = modelData.value
                            }
                        }
                    }
                }
            }
        }
    }

'''
    if marker not in s:
        raise SystemExit("RCRSSI Row marker not found")
    s = s.replace(marker, menu + marker, 1)

if "id: digitalDehazeButton" not in s:
    sig = '''        SignalStrength {
            anchors.verticalCenter: parent.verticalCenter
            size:                   parent.height * 0.5
            percent:                _rcRSSIAvailable ? _activeVehicle.rcRSSI : 0
        }
'''
    button = r'''
        Rectangle {
            id: digitalDehazeButton
            z: 20
            width: ScreenTools.defaultFontPixelWidth * 8.7
            height: parent.height * 0.92
            anchors.verticalCenter: parent.verticalCenter
            radius: ScreenTools.defaultFontPixelWidth * 0.35
            color: mainWindow.customDehazeMode !== "off" ? "#1f7a45" : Qt.rgba(0,0,0,0.08)
            border.width: 1
            border.color: mainWindow.customDehazeMode !== "off" ? "#00ff66" : qgcPal.buttonText

            Column {
                anchors.centerIn: parent
                spacing: -ScreenTools.defaultFontPixelHeight * 0.08

                QGCLabel {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "Digital"
                    color: "white"
                    font.pointSize: ScreenTools.smallFontPointSize
                    font.family: ScreenTools.demiboldFontFamily
                }

                QGCLabel {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "Dehazing"
                    color: "white"
                    font.pointSize: ScreenTools.smallFontPointSize
                    font.family: ScreenTools.demiboldFontFamily
                }
            }

            MouseArea {
                anchors.fill: parent
                onClicked: mainWindow.showIndicatorPopup(digitalDehazeButton, digitalDehazeInfo)
            }
        }
'''
    if sig not in s:
        raise SystemExit("RCRSSI SignalStrength marker not found")
    s = s.replace(sig, sig + button, 1)

s = s.replace('''    Row {
        id:             rssiRow
        anchors.top:    parent.top
''',
'''    Row {
        id:             rssiRow
        z:              2
        anchors.top:    parent.top
''', 1)
s = s.replace('''    MouseArea {
        anchors.fill:   parent
''',
'''    MouseArea {
        z:              1
        anchors.fill:   parent
''', 1)
write(p, s)

# Single-pass GPU dehaze for the main decoded video.
p = "src/FlightDisplay/FlightDisplayViewVideo.qml"
s = read(p)
if "id: videoLoader" not in s:
    s = s.replace(
'''        Loader {
            // GStreamer is causing crashes''',
'''        Loader {
            id: videoLoader
            // GStreamer is causing crashes''', 1)

if "id: digitalDehazeEffect" not in s:
    marker = '''        //-- Thermal Image
'''
    shader = r'''        ShaderEffectSource {
            id: digitalDehazeSource
            anchors.fill: videoLoader
            sourceItem: videoLoader
            live: true
            smooth: true
            hideSource: mainWindow.customDehazeMode !== "off"
            visible: mainWindow.customDehazeMode !== "off"
        }

        ShaderEffect {
            id: digitalDehazeEffect
            anchors.fill: videoLoader
            visible: mainWindow.customDehazeMode !== "off" && QGroundControl.videoManager.decoding

            property variant source: digitalDehazeSource
            property real strength: mainWindow.customDehazeMode === "low" ? 0.28
                                  : mainWindow.customDehazeMode === "medium" ? 0.52
                                  : mainWindow.customDehazeMode === "high" ? 0.82
                                  : 0.55
            property real autoMode: mainWindow.customDehazeMode === "auto" ? 1.0 : 0.0
            property vector2d texel: Qt.vector2d(1.0 / Math.max(1.0, width),
                                                 1.0 / Math.max(1.0, height))

            fragmentShader: "varying highp vec2 qt_TexCoord0;\n"
                          + "uniform sampler2D source;\n"
                          + "uniform lowp float qt_Opacity;\n"
                          + "uniform highp float strength;\n"
                          + "uniform highp float autoMode;\n"
                          + "uniform highp vec2 texel;\n"
                          + "void main() {\n"
                          + "  highp vec2 uv = qt_TexCoord0;\n"
                          + "  highp vec3 c0 = texture2D(source, uv).rgb;\n"
                          + "  highp vec3 n = (texture2D(source, uv + vec2(texel.x,0.0)).rgb"
                          + " + texture2D(source, uv - vec2(texel.x,0.0)).rgb"
                          + " + texture2D(source, uv + vec2(0.0,texel.y)).rgb"
                          + " + texture2D(source, uv - vec2(0.0,texel.y)).rgb) * 0.25;\n"
                          + "  highp float l0 = dot(c0, vec3(0.299,0.587,0.114));\n"
                          + "  highp float dark = min(c0.r, min(c0.g, c0.b));\n"
                          + "  highp float local = clamp(length(c0 - n) * 3.0, 0.0, 1.0);\n"
                          + "  highp float haze = clamp(dark * 1.15 + (1.0-local) * 0.18 - 0.16, 0.0, 1.0);\n"
                          + "  highp float s = strength;\n"
                          + "  if (autoMode > 0.5) s = clamp(0.18 + haze * 0.62, 0.18, 0.78);\n"
                          + "  highp float black = clamp(0.035 + haze * 0.09, 0.0, 0.16) * s;\n"
                          + "  highp vec3 c = (c0 - vec3(black)) / max(0.72, 1.0 - black);\n"
                          + "  highp float lum = dot(c, vec3(0.299,0.587,0.114));\n"
                          + "  c = mix(vec3(lum), c, 1.0 + 0.20*s);\n"
                          + "  c = (c - 0.5) * (1.0 + 0.32*s) + 0.5;\n"
                          + "  c += (c0 - n) * (0.12 + 0.28*s);\n"
                          + "  c = pow(max(c, vec3(0.0)), vec3(1.0/(1.0 + 0.08*s)));\n"
                          + "  highp float guard = smoothstep(0.025, 0.16, l0);\n"
                          + "  c = mix(c0, c, guard);\n"
                          + "  gl_FragColor = vec4(clamp(c,0.0,1.0),1.0) * qt_Opacity;\n"
                          + "}\n"
        }

'''
    if marker not in s:
        raise SystemExit("Thermal marker not found for dehaze shader")
    s = s.replace(marker, shader + marker, 1)
write(p, s)

print("Digital Dehazing + X-Target patch applied")


# ===========================================================================
# X_TARGET_UI_V2
# Match the compact reference reticle and expose Digital Dehazing as its own
# toolbar indicator. The previous in-RCRSSI button is hidden.
# ===========================================================================

# Replace the oversized reticle with the compact reference-style X-Target.
p = "src/FlightDisplay/FlightDisplayViewVideo.qml"
s = read(p)
start = s.find("    Canvas {\n        id: customReticle")
end = s.find("\n    property var _customVehicle:", start)
if start < 0 or end < 0:
    raise SystemExit("Could not locate customReticle block")

reticle_v2 = r'''    Canvas {
        id: customReticle
        anchors.fill: parent
        z: 900
        visible: QGroundControl.settingsManager.flyViewSettings.targetSize.rawValue !== "none"

        property string targetSize: QGroundControl.settingsManager.flyViewSettings.targetSize.rawValue
        property string targetColor: QGroundControl.settingsManager.flyViewSettings.targetColor.rawValue

        onTargetSizeChanged: requestPaint()
        onTargetColorChanged: requestPaint()
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()

            var cx = width / 2
            var cy = height / 2
            var reticleColor = targetColor === "green" ? "#00ff00"
                             : targetColor === "white" ? "#ffffff"
                             : targetColor === "yellow" ? "#ffff00"
                             : targetColor === "cyan" ? "#00e5ff"
                             : "#ff0000"

            ctx.strokeStyle = reticleColor
            ctx.fillStyle = reticleColor
            ctx.lineWidth = 2

            if (targetSize === "x-target") {
                // Compact proportions based on the supplied reference image.
                var scale = Math.max(0.85, Math.min(1.25, Math.min(width, height) / 900.0))
                var hx = 96 * scale
                var hy = 92 * scale
                var gap = 8 * scale
                var stepX = 15 * scale
                var stepY = 14 * scale

                // Main cross with a small clear centre.
                ctx.beginPath()
                ctx.moveTo(cx-hx, cy);     ctx.lineTo(cx-gap, cy)
                ctx.moveTo(cx+gap, cy);    ctx.lineTo(cx+hx, cy)
                ctx.moveTo(cx, cy-hy);     ctx.lineTo(cx, cy-gap)
                ctx.moveTo(cx, cy+gap);    ctx.lineTo(cx, cy+hy)
                ctx.stroke()

                // Graduated ticks on both axes.
                for (var i = 1; i <= 6; i++) {
                    var ox = i * stepX
                    var oy = i * stepY
                    var tx = (i % 3 === 0 ? 14 : 9) * scale
                    var ty = (i % 3 === 0 ? 14 : 9) * scale

                    ctx.beginPath()
                    ctx.moveTo(cx-ox, cy-tx/2); ctx.lineTo(cx-ox, cy+tx/2)
                    ctx.moveTo(cx+ox, cy-tx/2); ctx.lineTo(cx+ox, cy+tx/2)
                    ctx.moveTo(cx-ty/2, cy-oy); ctx.lineTo(cx+ty/2, cy-oy)
                    ctx.moveTo(cx-ty/2, cy+oy); ctx.lineTo(cx+ty/2, cy+oy)
                    ctx.stroke()
                }

                // Slightly longer end caps as in the reference sight.
                ctx.beginPath()
                ctx.moveTo(cx-hx, cy-13*scale); ctx.lineTo(cx-hx, cy+13*scale)
                ctx.moveTo(cx+hx, cy-13*scale); ctx.lineTo(cx+hx, cy+13*scale)
                ctx.moveTo(cx-13*scale, cy-hy); ctx.lineTo(cx+13*scale, cy-hy)
                ctx.moveTo(cx-13*scale, cy+hy); ctx.lineTo(cx+13*scale, cy+hy)
                ctx.stroke()

                // Four pairs of floating horizontal reference marks.
                var levels = [42, 63]
                var xMarks = [49, 77]
                for (var l = 0; l < levels.length; l++) {
                    var yy = levels[l] * scale
                    for (var m = 0; m < xMarks.length; m++) {
                        var xx = xMarks[m] * scale
                        var dash = (m === 0 ? 14 : 18) * scale
                        ctx.beginPath()
                        ctx.moveTo(cx-xx-dash/2, cy-yy); ctx.lineTo(cx-xx+dash/2, cy-yy)
                        ctx.moveTo(cx+xx-dash/2, cy-yy); ctx.lineTo(cx+xx+dash/2, cy-yy)
                        ctx.moveTo(cx-xx-dash/2, cy+yy); ctx.lineTo(cx-xx+dash/2, cy+yy)
                        ctx.moveTo(cx+xx-dash/2, cy+yy); ctx.lineTo(cx+xx+dash/2, cy+yy)
                        ctx.stroke()
                    }
                }

                // Small X in the centre.
                ctx.lineWidth = 2.4
                ctx.beginPath()
                ctx.moveTo(cx-5*scale, cy-5*scale); ctx.lineTo(cx+5*scale, cy+5*scale)
                ctx.moveTo(cx+5*scale, cy-5*scale); ctx.lineTo(cx-5*scale, cy+5*scale)
                ctx.stroke()
                return
            }

            // Preserve the standard compact reticles.
            var radius = 30
            var extent = 0
            var ticks = 0
            if (targetSize === "small") { extent = 150; ticks = 8 }
            else if (targetSize === "medium") { extent = 240; ticks = 12 }
            else if (targetSize === "large") { extent = 480; ticks = 20 }

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
                for (var j=0; j<ticks; j++) {
                    var sz = (j % 2 === 0) ? 12 : 20
                    var o = radius + step + j * step
                    ctx.beginPath()
                    ctx.moveTo(cx-sz/2, cy-o); ctx.lineTo(cx+sz/2, cy-o)
                    ctx.moveTo(cx-sz/2, cy+o); ctx.lineTo(cx+sz/2, cy+o)
                    ctx.moveTo(cx-o, cy-sz/2); ctx.lineTo(cx-o, cy+sz/2)
                    ctx.moveTo(cx+o, cy-sz/2); ctx.lineTo(cx+o, cy+sz/2)
                    ctx.stroke()
                }
            }
        }
    }
'''
s = s[:start] + reticle_v2 + s[end:]
write(p, s)

# Hide the first experimental dehaze button embedded inside RCRSSIIndicator.
p = "src/ui/toolbar/RCRSSIIndicator.qml"
s = read(p)
if "id: digitalDehazeButton" in s and "id: digitalDehazeButton\n            visible: false" not in s:
    s = s.replace("id: digitalDehazeButton\n            z: 20",
                  "id: digitalDehazeButton\n            visible: false\n            z: 20", 1)
write(p, s)

# Standalone toolbar indicator. When a vehicle is connected FirmwarePlugin puts
# it immediately after RC RSSI. A disconnected fallback is added below.
digital_indicator = r'''import QtQuick 2.12
import QGroundControl 1.0
import QGroundControl.Controls 1.0
import QGroundControl.Palette 1.0
import QGroundControl.ScreenTools 1.0

Rectangle {
    id: root

    property bool showIndicator: true
    property bool active: mainWindow.customDehazeMode !== "off"

    implicitWidth: ScreenTools.defaultFontPixelWidth * 9.0
    implicitHeight: parent ? parent.height : ScreenTools.defaultFontPixelHeight * 2.4
    radius: ScreenTools.defaultFontPixelWidth * 0.35
    color: active ? "#1f7a45" : Qt.rgba(0,0,0,0.08)
    border.width: 1
    border.color: active ? "#00ff66" : qgcPal.buttonText

    QGCPalette {
        id: qgcPal
        colorGroupEnabled: true
    }

    Column {
        anchors.centerIn: parent
        spacing: -ScreenTools.defaultFontPixelHeight * 0.10

        QGCLabel {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "Digital"
            color: "white"
            font.pointSize: ScreenTools.smallFontPointSize
            font.family: ScreenTools.demiboldFontFamily
        }

        QGCLabel {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "Dehazing"
            color: "white"
            font.pointSize: ScreenTools.smallFontPointSize
            font.family: ScreenTools.demiboldFontFamily
        }
    }

    MouseArea {
        anchors.fill: parent
        onClicked: {
            if (mainWindow.customDehazeMode === "off") {
                mainWindow.customDehazeMode = "auto"
            }
            mainWindow.showIndicatorPopup(root, digitalDehazePopup)
        }
    }

    Component {
        id: digitalDehazePopup

        Rectangle {
            width: ScreenTools.defaultFontPixelWidth * 32
            height: menuColumn.implicitHeight + ScreenTools.defaultFontPixelHeight * 2
            radius: ScreenTools.defaultFontPixelHeight * 0.5
            color: qgcPal.window
            border.width: 1
            border.color: qgcPal.text

            Column {
                id: menuColumn
                anchors.centerIn: parent
                spacing: ScreenTools.defaultFontPixelHeight * 0.45

                QGCLabel {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "DIGITAL DEHAZING"
                    color: qgcPal.text
                    font.family: ScreenTools.demiboldFontFamily
                }

                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: ScreenTools.defaultFontPixelWidth * 0.7

                    Repeater {
                        model: [
                            { "label": "OFF", "mode": "off" },
                            { "label": "AUTO", "mode": "auto" }
                        ]

                        Rectangle {
                            width: ScreenTools.defaultFontPixelWidth * 9
                            height: ScreenTools.defaultFontPixelHeight * 2
                            radius: ScreenTools.defaultFontPixelWidth * 0.35
                            color: mainWindow.customDehazeMode === modelData.mode ? "#1f7a45" : qgcPal.button
                            border.width: 1
                            border.color: mainWindow.customDehazeMode === modelData.mode ? "#00ff66" : qgcPal.text

                            QGCLabel {
                                anchors.centerIn: parent
                                text: modelData.label
                                color: mainWindow.customDehazeMode === modelData.mode ? "white" : qgcPal.buttonText
                                font.family: ScreenTools.demiboldFontFamily
                            }

                            MouseArea {
                                anchors.fill: parent
                                onClicked: mainWindow.customDehazeMode = modelData.mode
                            }
                        }
                    }
                }

                QGCLabel {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "MANUAL"
                    color: qgcPal.text
                    font.family: ScreenTools.demiboldFontFamily
                }

                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: ScreenTools.defaultFontPixelWidth * 0.5

                    Repeater {
                        model: [
                            { "label": "LOW", "mode": "low" },
                            { "label": "MEDIUM", "mode": "medium" },
                            { "label": "HIGH", "mode": "high" }
                        ]

                        Rectangle {
                            width: ScreenTools.defaultFontPixelWidth * 8.5
                            height: ScreenTools.defaultFontPixelHeight * 2
                            radius: ScreenTools.defaultFontPixelWidth * 0.35
                            color: mainWindow.customDehazeMode === modelData.mode ? "#1f7a45" : qgcPal.button
                            border.width: 1
                            border.color: mainWindow.customDehazeMode === modelData.mode ? "#00ff66" : qgcPal.text

                            QGCLabel {
                                anchors.centerIn: parent
                                text: modelData.label
                                color: mainWindow.customDehazeMode === modelData.mode ? "white" : qgcPal.buttonText
                                font.pointSize: ScreenTools.smallFontPointSize
                                font.family: ScreenTools.demiboldFontFamily
                            }

                            MouseArea {
                                anchors.fill: parent
                                onClicked: mainWindow.customDehazeMode = modelData.mode
                            }
                        }
                    }
                }

                QGCLabel {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "X-TARGET COLOR"
                    color: qgcPal.text
                    font.family: ScreenTools.demiboldFontFamily
                }

                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: ScreenTools.defaultFontPixelWidth * 0.9

                    Repeater {
                        model: [
                            { "value": "red", "colorValue": "#ff0000" },
                            { "value": "green", "colorValue": "#00ff00" },
                            { "value": "white", "colorValue": "#ffffff" },
                            { "value": "yellow", "colorValue": "#ffff00" },
                            { "value": "cyan", "colorValue": "#00e5ff" }
                        ]

                        Rectangle {
                            width: ScreenTools.defaultFontPixelHeight * 1.45
                            height: width
                            radius: width / 2
                            color: modelData.colorValue
                            border.width: QGroundControl.settingsManager.flyViewSettings.targetColor.rawValue === modelData.value ? 3 : 1
                            border.color: qgcPal.text

                            MouseArea {
                                anchors.fill: parent
                                onClicked: QGroundControl.settingsManager.flyViewSettings.targetColor.rawValue = modelData.value
                            }
                        }
                    }
                }
            }
        }
    }
}
'''
write("src/ui/toolbar/DigitalDehazingIndicator.qml", digital_indicator)

# Add the new QML to the resource collection.
s = read("qgroundcontrol.qrc")
needle = '        <file alias="RCRSSIIndicator.qml">src/ui/toolbar/RCRSSIIndicator.qml</file>\n'
if 'alias="DigitalDehazingIndicator.qml"' not in s:
    if needle not in s:
        raise SystemExit("RCRSSI qrc entry not found")
    s = s.replace(needle, needle + '        <file alias="DigitalDehazingIndicator.qml">src/ui/toolbar/DigitalDehazingIndicator.qml</file>\n', 1)
write("qgroundcontrol.qrc", s)

# Put Digital Dehazing immediately after RC RSSI in the vehicle toolbar list.
p = "src/FirmwarePlugin/FirmwarePlugin.cc"
s = read(p)
needle = '            QVariant::fromValue(QUrl::fromUserInput("qrc:/toolbar/RCRSSIIndicator.qml")),\n'
if 'qrc:/toolbar/DigitalDehazingIndicator.qml' not in s:
    if needle not in s:
        raise SystemExit("FirmwarePlugin RCRSSI list entry not found")
    s = s.replace(needle,
                  needle + '            QVariant::fromValue(QUrl::fromUserInput("qrc:/toolbar/DigitalDehazingIndicator.qml")),\n', 1)
write(p, s)

# While disconnected there is no vehicle indicator list, so show one fallback
# button. It disappears as soon as a vehicle connects.
p = "src/ui/toolbar/MainToolBarIndicators.qml"
s = read(p)
if "id: disconnectedDigitalDehazing" not in s:
    marker = '''    Repeater {
        id:     toolIndicatorsRepeater
'''
    fallback = '''    DigitalDehazingIndicator {
        id: disconnectedDigitalDehazing
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        visible: !_activeVehicle
    }

'''
    if marker not in s:
        raise SystemExit("Main toolbar vehicle repeater marker not found")
    s = s.replace(marker, fallback + marker, 1)
write(p, s)

print("X-Target UI v2 applied")
