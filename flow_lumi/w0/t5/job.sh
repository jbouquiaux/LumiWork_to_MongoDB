#!/bin/bash

#SBATCH --partition=batch
#SBATCH --job-name=w0_t5
#SBATCH --ntasks=128
#SBATCH --mem-per-cpu=1900
#SBATCH --time=0-1:0:0
#SBATCH --account=leds
#SBATCH --output=/gpfs/projects/acad/leds/DataBase_examples/adding_entry_to_DB/flow_lumi/w0/t5/queue.qout
#SBATCH --error=/gpfs/projects/acad/leds/DataBase_examples/adding_entry_to_DB/flow_lumi/w0/t5/queue.qerr
cd /gpfs/projects/acad/leds/DataBase_examples/adding_entry_to_DB/flow_lumi/w0/t5
# OpenMp Environment
export OMP_NUM_THREADS=1
# Commands before execution
source /gpfs/home/acad/ucl-modl/jbouq/abinit-9.10.5/build/modules.txt
export PATH=/gpfs/home/acad/ucl-modl/jbouq/abinit-9.10.5/build/src/98_main:$PATH

mpirun  -n 128 abinit /gpfs/projects/acad/leds/DataBase_examples/adding_entry_to_DB/flow_lumi/w0/t5/run.abi --timelimit 0-1:0:0  > /gpfs/projects/acad/leds/DataBase_examples/adding_entry_to_DB/flow_lumi/w0/t5/run.log 2> /gpfs/projects/acad/leds/DataBase_examples/adding_entry_to_DB/flow_lumi/w0/t5/run.err
