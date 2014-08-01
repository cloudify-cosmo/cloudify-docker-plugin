#!/bin/bash

f(){
    echo $1 >&2
    sleep 1
    exit $2
}

trap 'f TERM 1' TERM

for i in {1..2}; do
    for j in {1..1000}; do
        echo -n 'oooooooooooooooooooooooo';
        echo -n 'eeeeeeeeeeeeeeeeeeeeee' >&2;
    done; 
    echo "oooooooooo $i ooooooooooooo"; 
    echo "eeeeeeeeeeeeeeee $i eeeeeeeeeeeee" >&2; 
    sleep 1;
done
for i in {1..100}; do sleep 1; done
exit 0
