#!/bin/bash
# Silent setup for demo 1 - runs during shell init, invisible to VHS
export PS1='user my-project % '
export ACUMEN_ROOT=/Users/thomasallicino/oss/acumen
export PATH=$ACUMEN_ROOT/demos/bin:$PATH
rm -rf /tmp/acumen-demo1 2>/dev/null
python3 $ACUMEN_ROOT/demos/gen_fixture.py --state 1 --dir /tmp/acumen-demo1 >/dev/null 2>&1
cd /tmp/acumen-demo1
clear
