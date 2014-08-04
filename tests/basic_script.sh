#!/bin/bash

f(){
    echo ' terminate ';
    echo ' terminate ' >&2;
    for i in $(seq 1 $1); do sleep 1; done
    exit 10
}

trap "f $2" TERM
for i in {1..2}; do
    #for j in {1..1000}; do
        #echo -n ' test stdout ';
        #echo -n ' test stderr ' >&2;
    #done;
    echo " stdout $i ";
    echo " stderr $i " >&2;
    for k in $(seq 1 $1); do sleep 1; done
done
exit 0
