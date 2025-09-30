#!/bin/bash
#

source activate base

conda activate SFAIR

cd ./SFAIR/assessor
python3 assessor.py
