#!/bin/bash

echo $`pwd`: start cleaning

find $1 -name '*.pyc' -exec rm {} \;

echo done
