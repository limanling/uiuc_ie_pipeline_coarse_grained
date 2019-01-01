#!/usr/bin/env bash
# Please ensure that you are under aida_pipeline root folder.
mkdir data/test/relation
python aida_relation/gail_relation_test.py -l data/test/ltf_lst -f data/test/ltf -e data/test/edl/merged.cs -t data/test/edl/merged.tab -o data/test/relation/en.rel.cs
