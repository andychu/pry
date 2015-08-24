#!/bin/bash

publish() {
  cp --verbose pry/pry.py ../polyweb/deps 
}

unit() {
  "$@"
}

"$@"
