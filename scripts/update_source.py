#!/usr/bin/env python3

import json
import pathlib
import re
import sys
import urllib.request

OWNER = "NuvioMedia"
REPO = "NuvioMobile"

BUNDLE_ID = "com.nuvio.media"
MIN_OS = "16.1"
ICON_URL = "https://raw.githubusercontent.com/ohaiibuzzle/Nuvio-AltSource/main/icon.png"

SOURCE = {
    "name": "Nuvio",
    "identifier": "com.ohaiibuzzle.nuvio",
    "subtitle": "Nuvio Mobile unofficial AltSource (not affiliated)",
    "description": "Automatically tracks the newest iOS IPA published on github.com/NuvioMedia/NuvioMobile.",
}
SOURCE_URL = f"https://raw.githubusercontent.com/ohaiibuzzle/Nuvio-AltSource/main/apps.json"
OUT = pathlib.Path(__file__).resolve().parent.parent / "apps.json"


def api(path):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{OWNER}/{REPO}/{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "nuvio-altsource-updater",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def pick_ipa(release):
    ipas = [a for a in release.get("assets", []) if a["name"].lower().endswith(".ipa")]
    if not ipas:
        return None
    ipas.sort(key=lambda a: ("full" not in a["name"].lower(), -a["size"]))
    return ipas[0]


def version_of(tag):
    m = re.match(r"^v?(\d+(?:\.\d+)*)", tag or "")
    return m.group(1) if m else (tag or "").lstrip("v")


def main():
    release, ipa = None, None
    for candidate in api("releases?per_page=30"):
        if candidate.get("draft") or candidate.get("prerelease"):
            continue
        asset = pick_ipa(candidate)
        if asset:
            release, ipa = candidate, asset
            break

    if not release:
        sys.exit("No published release with an .ipa asset found.")

    version = version_of(release["tag_name"])
    payload = {
        "name": SOURCE["name"],
        "identifier": SOURCE["identifier"],
        "subtitle": SOURCE["subtitle"],
        "description": SOURCE["description"],
        "sourceURL": SOURCE_URL,
        "apps": [
            {
                "name": "Nuvio",
                "bundleIdentifier": BUNDLE_ID,
                "developerName": "Nuvio",
                "subtitle": "Media streaming client",
                "localizedDescription": f"Latest Nuvio build ({version}), pulled automatically from the official GitHub releases.",
                "iconURL": ICON_URL,
                "tintColor": "#5B4BFF",
                "versions": [
                    {
                        "version": version,
                        "date": release["published_at"],
                        "downloadURL": ipa["browser_download_url"],
                        "size": ipa["size"],
                        "minOSVersion": MIN_OS,
                    }
                ],
            }
        ],
    }

    text = json.dumps(payload, indent=2) + "\n"
    if OUT.exists() and OUT.read_text() == text:
        print(f"No change (still {version}).")
        return
    OUT.write_text(text)
    print(f"Wrote apps.json -> {version} ({ipa['name']}, {ipa['size']} bytes)")


if __name__ == "__main__":
    main()
