#!/usr/bin/env bash
# Please ensure that you are under aida_pipeline root folder.
#mkdir data/
#python aida_event_coreference/gail_event_coreference_test_en.py -i /nas/data/m1/lud2/AIDA/pilot/seedling/timeex/en_full_timex.cs -o /nas/data/m1/lud2/AIDA/pilot/seedling/timeex/en_events_xdoc_coreference.cs -r /nas/data/m1/AIDA_Data/aida2018/evaluation/source/en_rsd -n 50 -x
python aida_event_coreference/gail_event_coreference_test_ru.py -i /nas/data/m1/AIDA_Data/aida2018/evaluation/0922_R1_rerun/ru/ru_full.cs -o /nas/data/m1/lud2/AIDA/pilot/seedling/timeex/ru_events_xdoc_coreference.cs -r /nas/data/m1/AIDA_Data/aida2018/evaluation/source/ru_rsd -n 50 -x
