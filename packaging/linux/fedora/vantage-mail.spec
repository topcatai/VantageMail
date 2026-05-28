Name:           vantage-mail
Version:        1.0.1
Release:        1%{?dist}
Summary:        Vantage Mail Email Client

License:        Proprietary
URL:            https://github.com/yourusername/vantage-mail
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
Requires:       python3
Requires:       python3-pyqt6
Requires:       python3-pyqt6-webengine
Requires:       python3-msal
Requires:       python3-requests
Requires:       python3-icalendar
Requires:       python3-imapclient

%description
An Outlook-inspired email client with Exchange, SMTP, and IMAP integration.

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_datadir}/vantage-mail
mkdir -p %{buildroot}%{_datadir}/applications
mkdir -p %{buildroot}%{_datadir}/pixmaps

# Copy source and assets
cp -r src %{buildroot}%{_datadir}/vantage-mail/
cp -r "icons_Vantage Mail" %{buildroot}%{_datadir}/vantage-mail/

# Create binary wrapper
cat << 'EOF' > %{buildroot}%{_bindir}/vantage-mail
#!/bin/bash
export PYTHONPATH="%{_datadir}/vantage-mail/src:$PYTHONPATH"
exec python3 %{_datadir}/vantage-mail/src/main.py "$@"
EOF
chmod +x %{buildroot}%{_bindir}/vantage-mail

# Copy desktop launcher and icon
cp packaging/linux/vantage-mail.desktop %{buildroot}%{_datadir}/applications/
cp "icons_Vantage Mail/Vantage trans_Logo.png" %{buildroot}%{_datadir}/pixmaps/vantage-mail.png

%files
%{_bindir}/vantage-mail
%{_datadir}/vantage-mail
%{_datadir}/applications/vantage-mail.desktop
%{_datadir}/pixmaps/vantage-mail.png

%changelog
* Wed May 27 2026 Developer <dev@example.com> - 1.0.1-1
- Bugfix release for batch syncing, window lifetimes, and shortcut icons.

* Tue May 26 2026 Developer <dev@example.com> - 1.0.0-1
- Initial release of Vantage Mail desktop package.
