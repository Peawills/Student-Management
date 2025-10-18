Running the dev server safely (no HTTPS required)
===============================================

If you see "You're accessing the development server over HTTPS, but it only supports HTTP" in the console,
that means a TLS ClientHello reached the dev server (often because the server was bound to 0.0.0.0 or the browser
tried https://). To avoid that and run like before, run the server bound to localhost only.

Windows PowerShell (recommended):

    .\env\Scripts\Activate.ps1
    .\runserver-local.ps1

Or using the batch helper:

    runserver-local.bat

These helpers start Django on 127.0.0.1:8000 so only local connections are accepted. Open http://127.0.0.1:8000 in your browser.

If you need HTTPS for testing later, use ngrok or add a local self-signed cert via openssl and django-sslserver (optional).
