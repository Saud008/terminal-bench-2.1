#!/usr/bin/env bash
tmux kill-session -t zmrk3 2>/dev/null
tmux new-session -d -s zmrk3 "bash -lc 'SLUG=zonefile-master-repair bash ~/runk.sh 3 > ~/tbruns/zmr-k3-driver.log 2>&1'"
sleep 30
tail -c 400 ~/tbruns/zmr-k3-driver.log
