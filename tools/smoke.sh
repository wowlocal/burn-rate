#!/bin/zsh
# Burn Rate's smoke check: a scripted headless VS match against the computer
# (player 1 Blitz, the computer on Random), with a signature special early on
# and player 1 punching every 40 cycles, run until 3000 loaded cycles.
# Passes when the match launches, ends (an epilogue back to the menu) and its
# replay is written. Usage: tools/smoke.sh [BUILD_DIR]   (default build/)
set -u
B=${1:-${0:A:h:h}/build}
R=$B/runs/smoke; rm -rf $R; mkdir -p $R/overlay
A=65; RT=39; UP=38; D=68
LS="4 hold $A 1; 10 hold $A 1; 14 hold $RT 1; 18 hold $A 1; 22 hold $A 1; 182 hold $A 1; 188 hold $RT 1; 192 hold $RT 1"
LS="$LS; 196 hold $RT 1; 200 hold $A 1; 204 hold $A 1; 210 hold $UP 1; 214 hold $UP 1; 218 hold $A 1"
LS="$LS; 300 hold $D 1; 302 hold $RT 1; 304 hold $A 1"
for c in $(seq 340 40 3000); do LS="$LS; $c hold $A 2"; done
$B/swiftpm/release/BurnRateHeadless --resources $B/content --music-dir $B/content/OriginalMusic --virtual-clock 123456789 8 \
  --no-network --mute-music --mute-sounds --overlay $R/overlay --script "8 click 398 229; 90000 exit" \
  --loaded-script "$LS; 3000 exit" > $R/run.log 2>&1
code=$?
launched=$(grep -c '"event":"matchLaunched"' $R/run.log); ended=$(grep -c '"event":"menu"' $R/run.log)
replays=$(ls $R/overlay/recording 2>/dev/null | wc -l | tr -d ' ')
echo "exit $code, matches launched $launched, ended $ended, replays $replays"
[ $code -eq 0 ] && [ $launched -ge 1 ] && [ $ended -ge 1 ] && [ $replays -ge 1 ] && echo "smoke: pass" || { echo "smoke: FAIL ($R/run.log)"; exit 1; }
