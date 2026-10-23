#!/bin/zsh
# Burn Rate's whole build, outputs on NTSD-Builds (never the internal disk):
#  1. tools/content/stage.py stages the content (raw Codex art from $BURNRATE_RAW);
#  2. BurnRateContentBuilder writes the eight engine packages and
#     Sources/BurnRateContent/GeneratedIdentity.swift;
#  3. swift build (release) of the app and the headless host;
#  4. BurnRate.app: the executable, the packages in Contents/Resources,
#     Info.plist, an ad-hoc signature.
# Usage: tools/build.sh [BUILD_DIR]
set -eu
REPO=${0:A:h:h}
B=${1:-/Volumes/NTSD-Builds/tasks/burnrate/build}
PY=${BURNRATE_PYTHON:-/Volumes/NTSD-Builds/tasks/burnrate/venv/bin/python}
XB=/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin
mkdir -p $B
cd $REPO
$PY tools/content/stage.py $B/stage
$XB/swift-build --scratch-path $B/swiftpm --build-system native -c release --product BurnRateContentBuilder > $B/builder-build.log 2>&1 \
  || { grep -E 'error:' $B/builder-build.log | head; exit 1; }
$B/swiftpm/release/BurnRateContentBuilder $B/stage $B/content Sources/BurnRateContent/GeneratedIdentity.swift
for product in BurnRate BurnRateHeadless; do
  $XB/swift-build --scratch-path $B/swiftpm --build-system native -c release --product $product > $B/$product-build.log 2>&1 \
    || { grep -E 'error:' $B/$product-build.log | head; exit 1; }
done
APP=$B/BurnRate.app
rm -rf $APP && mkdir -p $APP/Contents/MacOS $APP/Contents/Resources
cp $B/swiftpm/release/BurnRate $APP/Contents/MacOS/BurnRate
cp -R $B/content/* $APP/Contents/Resources/
cat > $APP/Contents/Info.plist <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleExecutable</key><string>BurnRate</string>
  <key>CFBundleIdentifier</key><string>local.burnrate.game</string>
  <key>CFBundleName</key><string>Burn Rate</string>
  <key>CFBundleDisplayName</key><string>Burn Rate</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>0.1</string>
  <key>CFBundleVersion</key><string>1</string>
  <key>LSMinimumSystemVersion</key><string>14.0</string>
  <key>NSHighResolutionCapable</key><true/>
</dict></plist>
PLIST
codesign --force --sign - $APP
echo "built $APP"
