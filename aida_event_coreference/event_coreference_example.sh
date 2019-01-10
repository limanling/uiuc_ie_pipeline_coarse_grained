#!/usr/bin/env bash
# Please ensure that you are under aida_pipeline root folder.
mkdir data/
python aida_event_coreference/gail_event_coreference_test_ukr.py -i data/uk_events.cs -o data/uk_events_coreference.cs
