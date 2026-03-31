#!/bin/bash
# Shell wrapper for demo 2 — VHS uses this as its shell
export PS1='user my-project % '
export ACUMEN_ROOT=/Users/thomasallicino/oss/acumen
export PATH=$ACUMEN_ROOT/demos/bin:$PATH
rm -rf /tmp/acumen-demo2 2>/dev/null
python3 $ACUMEN_ROOT/demos/gen_fixture.py --state 2 --dir /tmp/acumen-demo2 >/dev/null 2>&1
cd /tmp/acumen-demo2
exec /bin/bash --norc --noprofile
