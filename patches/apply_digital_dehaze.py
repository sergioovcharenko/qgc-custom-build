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
