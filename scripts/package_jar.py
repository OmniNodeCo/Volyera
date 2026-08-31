#!/usr/bin/env python3
"""Assemble the Volyera mod jar directly from resources.

Volyera is currently 100% data-driven, so the mod jar is just a zip of
src/main/resources plus a manifest. This script produces a jar identical in
function to the Gradle build's output, without needing a JDK.

Usage:  python3 scripts/package_jar.py [output.jar]
"""
import json
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "src", "main", "resources")


def main() -> None:
    with open(os.path.join(RES, "fabric.mod.json")) as f:
        meta = json.load(f)
    version = meta["version"]

    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        ROOT, "dist", f"volyera-{version}.jar")
    os.makedirs(os.path.dirname(out), exist_ok=True)

    # Validate every JSON resource before packaging.
    for dirpath, _dirnames, filenames in os.walk(RES):
        for name in filenames:
            if name.endswith(".json"):
                path = os.path.join(dirpath, name)
                with open(path) as f:
                    json.load(f)  # raises on malformed JSON

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as jar:
        jar.writestr(
            "META-INF/MANIFEST.MF",
            "Manifest-Version: 1.0\r\n"
            "Implementation-Title: volyera\r\n"
            f"Implementation-Version: {version}\r\n\r\n",
        )
        jar.write(os.path.join(ROOT, "LICENSE"), "LICENSE_volyera")
        for dirpath, _dirnames, filenames in os.walk(RES):
            for name in sorted(filenames):
                path = os.path.join(dirpath, name)
                arc = os.path.relpath(path, RES).replace(os.sep, "/")
                jar.write(path, arc)

    print(f"wrote {out}")


if __name__ == "__main__":
    main()
