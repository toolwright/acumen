#!/bin/bash
# Shell wrapper for demo 3 — VHS uses this as its shell
export PS1='user my-project % '
export ACUMEN_ROOT=/Users/thomasallicino/oss/acumen
export PATH=$ACUMEN_ROOT/demos/bin:$PATH
rm -rf /tmp/acumen-demo3 2>/dev/null
python3 $ACUMEN_ROOT/demos/gen_fixture.py --state 3 --dir /tmp/acumen-demo3 >/dev/null 2>&1
cd /tmp/acumen-demo3
exec /bin/bash --norc --noprofile
