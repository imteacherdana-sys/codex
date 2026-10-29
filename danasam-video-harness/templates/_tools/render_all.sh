#!/usr/bin/env bash
# 모든 템플릿 폴더를 렌더링하고 960x540 미리보기 MP4를 만든다.
set -u
cd "$(dirname "$0")/.."
mkdir -p _previews
for d in ${@:-*/}; do
  d=${d%/}
  [ -f "$d/index.html" ] || continue
  case "$d" in _*) continue;; esac
  ( cd "$d" && npx hyperframes render --quality looks --output "../_previews/$d.full.mp4" > "../_previews/$d.log" 2>&1 )
  if [ -s "_previews/$d.full.mp4" ]; then
    ffmpeg -loglevel error -y -i "_previews/$d.full.mp4" -vf scale=960:540 -c:v libx264 -crf 30 -preset veryfast -an -movflags +faststart "_previews/$d.mp4"
    rm -f "_previews/$d.full.mp4"
    echo "ok $d $(du -k "_previews/$d.mp4" | cut -f1)KB"
  else
    echo "FAIL $d"
  fi
done
echo ALL_DONE
