#!/bin/bash

# activate virtual environment
# cd /home/monitor/SFAIR_workspace/model_deploy
# source venv/bin/activate
source activate base
conda activate SFAIR

# set up remote model (should be on a CVM)
cd /home/monitor/SFAIR_workspace/model_deploy
cd app
gunicorn -b 127.0.0.1:5001 remote_keras:app

