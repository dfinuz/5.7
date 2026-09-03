DFIN DSKEYS Manager v5.7 diagnostic full installer.

This build:
- shows the high-quality DFIN logo at the real top-left of the app header
- uses the logo as the title-bar, shortcut, and installer icon
- installs Python 3.13.7 system-wide with pip, PATH, and the py launcher
- installs send2trash, cryptography, and websocket-client offline
- writes C:\Program Files\DFIN DSKEYS Manager\python-check.txt and python-install.log
- uses separate E-IMZO WebSocket connections for API-key registration and certificate listing
- tries localhost and 127.0.0.1 with multiple accepted origins and strict timeouts
- displays complete E-IMZO connection errors instead of hiding them
