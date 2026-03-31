# Demo 1: Observation -> Reflection -> Proposal
# Requires: python3 demos/gen_fixture.py --state 1 --dir /tmp/acumen-demo1

Output demos/demo1-observe-reflect.gif

Set Shell "bash"
Set FontSize 16
Set Width 900
Set Height 520
Set Padding 20
Set Theme { "name": "Acumen", "black": "#1a1b26", "red": "#f7768e", "green": "#9ece6a", "yellow": "#e0af68", "blue": "#7aa2f7", "magenta": "#bb9af7", "cyan": "#7dcfff", "white": "#c0caf5", "brightBlack": "#414868", "brightRed": "#f7768e", "brightGreen": "#9ece6a", "brightYellow": "#e0af68", "brightBlue": "#7aa2f7", "brightMagenta": "#bb9af7", "brightCyan": "#7dcfff", "brightWhite": "#c0caf5", "background": "#1a1b26", "foreground": "#c0caf5", "selection": "#33467c", "cursor": "#c0caf5" }

# Instant setup: set env, cd to fixture, clear screen
Set TypingSpeed 0ms
Type "export PS1='user my-project % ' ACUMEN_ROOT=/Users/thomasallicino/oss/acumen && export PATH=$ACUMEN_ROOT/demos/bin:$PATH && cd /tmp/acumen-demo1 && clear"
Enter
Sleep 800ms

# Demo starts clean
Set TypingSpeed 40ms

Type "acumen-status"
Sleep 400ms
Enter
Sleep 3s

Type "acumen-reflect"
Sleep 400ms
Enter
Sleep 4s

Type "acumen-status"
Sleep 400ms
Enter
Sleep 3s
