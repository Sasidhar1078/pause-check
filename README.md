# Pause & Check

A large-text, mobile-friendly scam-safety guide that can be installed as a
Progressive Web App (PWA). The website is served by a small Python backend that
also checks common URL warning signs.

## Run locally

Requires Python 3.10 or newer. The server uses only the Python standard library;
there are no packages to install.

From this folder, run:

```powershell
python app.py
```

Then open <http://127.0.0.1:8000>. To run the backend checks:

```powershell
python -m unittest -v
```

If `python` is not available in PowerShell, use the full path to your Python
executable for both commands.

## Save or share a copy

The **Download to this device** link saves `Pause-and-Check.html` as one
standalone page. Open that file with a current web browser on a phone, tablet,
or computer. Its scam-safety chat and basic link checks work without Python or
an internet connection. The standalone copy cannot be installed as an app or
use the hosted Python link-check endpoint.

## Privacy and limitations

The link-check endpoint analyses the address text only. It never visits the
destination, contacts a reputation service, or stores the submitted address.
Request logging is disabled. If the backend cannot be reached, the browser uses
a basic local check instead. No result can prove that a link is safe or genuine.

The server listens on the local computer by default. To install the PWA on a
phone, publish the site through an HTTPS host; browsers require a secure
connection to install an app and enable offline use. Do not expose the local
development server directly to the public internet.

## Publish a public, shareable website

This project includes a Render Blueprint at `render.yaml` for a public HTTPS
deployment. To publish it:

1. In Render, choose **New → Blueprint**.
2. Connect the GitHub repository containing this project.
3. Review the `pause-and-check` web service and choose **Apply**.
4. Wait for the health check at `/api/health` to pass. Render will provide a
   public HTTPS URL that works in phone and computer browsers.

The chat opens as the first section; visitors do not need to install the app.
Installation is optional. Share the Render HTTPS address for an online copy
that opens across devices, or use the download link for a standalone offline
copy. Hosting does not place the chat inside every unrelated website—it gives
everyone the same shareable website address. The assistant is a local
rules-based demo, not a connected AI model.
