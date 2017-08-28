#!/usr/bin/env bash

find couchdiscover -type f -name '*.py' -exec sed -i 's/ 2016 / 2017 /g' {} \;
