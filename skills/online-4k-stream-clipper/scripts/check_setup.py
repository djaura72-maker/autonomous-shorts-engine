#!/usr/bin/env python3
"""Check dependencies and hardware acceleration for online-4k-stream-clipper."""
import importlib
import shutil
import subprocess
import sys

PACKAGES = ["yt_dlp", "numpy"]
BINARIES = ["ffmpeg", "ffprobe", "yt-dlp"]

def check_videotoolbox():
    try:
        res = subprocess.run(["ffmpeg", "-encoders"], capture_output=True, text=True)
        if "h264_videotoolbox" in res.stdout:
            return True
    except Exception:
        pass
    return False

def main():
    print("🔍 Checking Online 4K Stream Clipper Dependencies...\n")
    missing_bins = []
    missing_pkgs = []
    
    for bin_name in BINARIES:
        path = shutil.which(bin_name)
        if path:
            print(f"  ✅ [Binary] {bin_name} -> {path}")
        else:
            print(f"  ❌ [Binary] {bin_name} NOT found in PATH")
            missing_bins.append(bin_name)
            
    for pkg in PACKAGES:
        try:
            importlib.import_module(pkg)
            print(f"  ✅ [Python] {pkg} -> installed")
        except ImportError:
            print(f"  ❌ [Python] {pkg} is NOT installed")
            missing_pkgs.append(pkg)
            
    has_vt = check_videotoolbox()
    if has_vt:
        print("  🚀 [Hardware Encoder] Apple Silicon VideoToolbox (h264_videotoolbox) available for ultra-fast 4K renders!")
    else:
        print("  ℹ️  [Software Encoder] libx264 will be used for rendering.")
        
    print("\n" + "="*50)
    if not missing_bins and not missing_pkgs:
        print("🎉 ALL SYSTEMS READY: Online 4K Stream Clipper is fully operational!")
        return 0
    else:
        print("⚠️  MISSING DEPENDENCIES:")
        if missing_bins:
            print(f"  Run: brew install {' '.join(missing_bins)}")
        if missing_pkgs:
            print(f"  Run: pip3 install {' '.join(missing_pkgs)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
