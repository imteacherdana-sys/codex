#!/usr/bin/env bash
# segments/*/ 를 renders/<폴더>.mp4로 렌더링한다. 이미 있으면 건너뛴다 (다시 하려면 지우고 실행).
# 사용: tools/render.sh [동시 작업 수, 기본 3]
set -u
cd "$(dirname "$0")/.."
export HYPERFRAMES_BROWSER_PATH=${HYPERFRAMES_BROWSER_PATH:-/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell}
export PRODUCER_HEADLESS_SHELL_PATH=${PRODUCER_HEADLESS_SHELL_PATH:-$HYPERFRAMES_BROWSER_PATH}
mkdir -p renders logs
JOBS=${1:-3}
render_one() {
  d=$1; n=$(basename "$d")
  [ -s "renders/$n.mp4" ] && { echo "skip $n"; return; }
  ( cd "$d" && npx hyperframes render --output "../../renders/$n.mp4" > "../../logs/$n.log" 2>&1 )
  if [ -s "renders/$n.mp4" ]; then echo "ok $n"; else echo "FAIL $n"; fi
}
export -f render_one
ls -d segments/*/ | sed 's:/$::' | xargs -P "$JOBS" -I{} bash -c 'render_one {}'
echo ALL_DONE
