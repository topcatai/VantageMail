#!/bin/bash
# Exit on error
set -e

# Build the .app bundle using py2app
python3 setup_app.py py2app

# Setup directories for DMG creation
APP_NAME="VantageMail"
DMG_NAME="${APP_NAME}.dmg"
DIST_DIR="dist"

# Remove old DMG if exists
rm -f "${DIST_DIR}/${DMG_NAME}"

# Create a temporary folder to mount
TMP_DMG_DIR="tmp_dmg"
rm -rf "${TMP_DMG_DIR}"
mkdir -p "${TMP_DMG_DIR}"

# Copy the app bundle to temporary folder
cp -R "${DIST_DIR}/${APP_NAME}.app" "${TMP_DMG_DIR}/"

# Create link to Applications folder
ln -s /Applications "${TMP_DMG_DIR}/Applications"

# Create the DMG using macOS native hdiutil tool
hdiutil create -volname "${APP_NAME} Installer" -srcfolder "${TMP_DMG_DIR}" -ov -format UDZO "${DIST_DIR}/${DMG_NAME}"

# Cleanup
rm -rf "${TMP_DMG_DIR}"

echo "macOS DMG installer ${DIST_DIR}/${DMG_NAME} built successfully!"
