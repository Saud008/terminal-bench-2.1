K="$1"
LOG=~/tbruns/pinwheel-launch-k$K.out
SLUG=pinwheel-semver-range-repair setsid nohup bash ~/runk.sh "$K" > "$LOG" 2>&1 < /dev/null &
echo "launched pid $! log $LOG"
