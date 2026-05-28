#!/bin/bash
# Exit on error
set -e

# Setup clean build directory
BUILD_DIR="build_deb_pkg"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$BUILD_DIR/usr/share/vantage-mail"
mkdir -p "$BUILD_DIR/usr/share/applications"
mkdir -p "$BUILD_DIR/usr/share/pixmaps"

# Copy debian control
cp debian/DEBIAN/control "$BUILD_DIR/DEBIAN/"

# Copy python source files and assets
cp -r ../../src "$BUILD_DIR/usr/share/vantage-mail/"
cp -r ../../"icons_Vantage Mail" "$BUILD_DIR/usr/share/vantage-mail/"

# Create executable wrapper
cat << 'EOF' > "$BUILD_DIR/usr/bin/vantage-mail"
#!/bin/bash
export PYTHONPATH="/usr/share/vantage-mail/src:$PYTHONPATH"
exec python3 /usr/share/vantage-mail/src/main.py "$@"
EOF
chmod +x "$BUILD_DIR/usr/bin/vantage-mail"

# Copy desktop launcher
cp vantage-mail.desktop "$BUILD_DIR/usr/share/applications/"

# Copy app icon to pixmaps
cp ../../"icons_Vantage Mail/Vantage trans_Logo.png" "$BUILD_DIR/usr/share/pixmaps/vantage-mail.png"

# Build package
dpkg-deb --build "$BUILD_DIR" vantage-mail_1.0.1_amd64.deb

echo "Debian package vantage-mail_1.0.1_amd64.deb built successfully!"
