#!/bin/bash
# Shell wrapper for demo 1 — VHS uses this as its shell
export PS1='user my-project % '
export ACUMEN_ROOT=/Users/thomasallicino/oss/acumen
export PATH=$ACUMEN_ROOT/demos/bin:$PATH
rm -rf /tmp/acumen-demo1 2>/dev/null
python3 $ACUMEN_ROOT/demos/gen_fixture.py --state 1 --dir /tmp/acumen-demo1 >/dev/null 2>&1
cd /tmp/acumen-demo1
exec /bin/bash --norc --noprofile
