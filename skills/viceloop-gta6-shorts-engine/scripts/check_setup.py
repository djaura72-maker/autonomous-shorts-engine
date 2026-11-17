#!/usr/bin/env python3
"""Check local system dependencies for viceloop-gta6-shorts-engine."""
import importlib
import shutil
import sys

PACKAGES = ["faster_whisper", "yt_dlp", "numpy"]
BINARIES = ["ffmpeg", "ffprobe"]

def main():
    missing_pkgs = []
    missing_bins = []
    
    print("🔍 Checking ViceLoop GTA VI Engine Dependencies...\n")
    
    for bin_name in BINARIES:
        path = shutil.which(bin_name)
        if path:
            print(f"  ✅ [Binary] {bin_name} -> {path}")
        else:
            print(f"  ❌ [Binary] {bin_name} is NOT found in PATH")
            missing_bins.append(bin_name)
            
    for pkg in PACKAGES:
        try:
            importlib.import_module(pkg)
            print(f"  ✅ [Python] {pkg} -> installed")
        except ImportError:
            print(f"  ❌ [Python] {pkg} is NOT installed")
            missing_pkgs.append(pkg)
            
    print("\n" + "="*50)
    if not missing_pkgs and not missing_bins:
        print("🎉 ALL SYSTEMS READY: ViceLoop GTA VI Engine is operational!")
        return 0
    else:
        print("⚠️  MISSING DEPENDENCIES DETECTED:")
        if missing_bins:
            print(f"  Install binaries with: brew install {' '.join(missing_bins)}")
        if missing_pkgs:
            print(f"  Install python libraries with: pip3 install {' '.join(missing_pkgs)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
