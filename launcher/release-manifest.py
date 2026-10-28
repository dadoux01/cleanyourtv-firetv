#!/usr/bin/env python3
"""Write the update.json the updater reads, from the APKs of a release.

    release-manifest.py <tag> launcher=<apk> updater=<apk> > update.json

Package name, versionCode and versionName come from `aapt2 dump badging` (AAPT2 or ANDROID_HOME's build-tools 34.0.0),
the SHA-256 from the file itself. The asset name is the APK's file name, so upload the APKs under these names.
"""
import hashlib
import json
import os
import re
import subprocess
import sys

BADGING = re.compile(r"^package: name='([^']+)' versionCode='(\d+)' versionName='([^']*)'", re.M)


def parse_badging(text):
    m = BADGING.search(text)
    if not m:
        raise ValueError("no package line in aapt2 output")
    return {"package": m.group(1), "versionCode": int(m.group(2)), "versionName": m.group(3)}


def aapt2():
    return os.environ.get("AAPT2") or os.path.join(os.environ["ANDROID_HOME"], "build-tools", "34.0.0", "aapt2")


def describe(path):
    out = subprocess.run([aapt2(), "dump", "badging", path], stdout=subprocess.PIPE, check=True,
                         universal_newlines=True).stdout
    info = parse_badging(out)
    with open(path, "rb") as f:
        info["sha256"] = hashlib.sha256(f.read()).hexdigest()
    info["file"] = os.path.basename(path)
    return info


def build(tag, apps):
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise ValueError("tag must look like v1.2.3: " + tag)
    return {"tag": tag, "apps": {role: describe(path) for role, path in apps}}


def main(argv):
    if len(argv) < 2 or any("=" not in a for a in argv[1:]):
        sys.stderr.write(__doc__)
        return 2
    apps = [a.split("=", 1) for a in argv[1:]]
    json.dump(build(argv[0], apps), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
