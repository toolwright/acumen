#!/bin/bash
# Render all demo GIFs using VHS
# Pre-generates fixture data, then records each demo
set -e
cd "$(dirname "$0")/.."

echo "Generating fixture data..."
python3 demos/gen_fixture.py --state 1 --dir /tmp/acumen-demo1
python3 demos/gen_fixture.py --state 2 --dir /tmp/acumen-demo2
python3 demos/gen_fixture.py --state 3 --dir /tmp/acumen-demo3

echo ""
echo "Rendering demo 1: Observation -> Reflection -> Proposal"
vhs demos/demo1.tape

echo "Rendering demo 2: Review -> Approve -> Rule Applied"
vhs demos/demo2.tape

echo "Rendering demo 3: Before/After Report"
vhs demos/demo3.tape

echo ""
echo "Done. GIFs:"
ls -lh demos/*.gif
