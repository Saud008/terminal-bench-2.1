#!/bin/bash
TASK='/mnt/d/Terminus-local-backup/tasks/nmea0183-multipart-talker-checksum-merge'
echo COUNT
find "$TASK" -type f | wc -l
echo STRUCTURE
find "$TASK" -type f | sort
echo '==== key files ===='
ls -la "$TASK/environment/Dockerfile" "$TASK/tests/test.sh" "$TASK/solution/solve.sh" "$TASK/tests/test_outputs.py" 2>&1
echo '==== solution ===='
ls -la "$TASK/solution/"
echo '==== zip in backup tasksubmit ===='
ls -la /mnt/d/Terminus-local-backup/tasksubmit/*nmea* 2>&1
