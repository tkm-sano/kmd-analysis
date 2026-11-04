#!/bin/bash
set -eu
out=$(cd "$(dirname "$0")/.." && pwd)
rt=/home/takuma/kmd-analysis/review_outputs/thesis_docx_integration_20261103/run01/rendering_tools
mkdir -p "$out/logs/cache" "$out/logs/config" "$out/render/profile"
export LD_LIBRARY_PATH="$rt/root/usr/lib/libreoffice/program:$rt/root/usr/lib/x86_64-linux-gnu"
export LD_PRELOAD="$rt/set_langtag.so"
export THESIS_LANGTAG_DATADIR="$rt/root/usr/share/liblangtag"
export SAL_USE_VCLPLUGIN=svp
export TMPDIR="$out/logs"
export XDG_CACHE_HOME="$out/logs/cache"
export XDG_CONFIG_HOME="$out/logs/config"
"$rt/root/usr/lib/libreoffice/program/soffice" "-env:UserInstallation=file://$out/render/profile" --headless --convert-to pdf --outdir "$out/render" "$out/THESIS_UPDATED_STEP3.docx"
