#!/bin/bash
export PRISM_ROOT="PRISMROOT"
export PRISM_AE_PLUGIN="PLUGINROOT"
"$PRISM_ROOT/Python313/bin/python3" "$PRISM_AE_PLUGIN"/Scripts/Prism_AfterEffects_MenuTools.py "$@"