#!/usr/bin/env bash
# Please ensure that you are under aida_pipeline root folder.
mkdir data/
python aida_nominal_coreference_en/gail_nominal_test.py --dev data/en.bio --dev_e data/en.linking.tab --out_e output.tab
