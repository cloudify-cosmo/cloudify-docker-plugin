#!/bin/bash

f(){
    echo ' terminate ';
    echo ' terminate ' >&2;
    for i in $(seq 1 $1); do sleep 1; done
    exit 10
}

trap "f $2" TERM
for i in {1..2}; do
    echo " stdout $i ";
    echo " stderr $i " >&2;
    for k in $(seq 1 $1); do sleep 1; done
done
exit 0
