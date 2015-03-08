#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import queries
from pykwalify.core import Core

from math import sqrt
from elasticsearch import Elasticsearch


def connect_to_es(ip):
    return Elasticsearch(ip)


def get_stats(settings, conn):
    conn.ping()

    query = queries.get_data_histogram_query(settings['time_aggregator'],
                                             settings['time_window'],
                                             settings["must"],
                                             settings["must_not"],
                                             settings["should"])
    res = conn.search(index="today", body=query)
    return res['aggregations']['events_by_date']['buckets']


def check_anomaly(sample, entries, std_multiply, chart_value='max'):
    n = 0
    mean = 0
    m2 = 0
    max_value = None
    for entry in entries:
        value = entry['stats_0'][chart_value]
        n += 1
        delta = value - mean
        mean += delta / n
        m2 += delta * (value - mean)
        max_value = max(max_value, value)
    variance = m2 / (n - 1)
    std = sqrt(variance)
    logging.info("sample: %s std : %s, mean : %s, max: %s, lol: %s" %
                 (sample['stats_0'][chart_value], std, mean, max_value, mean + 3 * std))
    if sample['stats_0'][chart_value] > mean + std_multiply * std:
        return sample
    else:
        return False


def load_settings():
    logging.info("Validating settings.yaml")
    c = Core(source_file="config/settings.yaml", schema_files=["config/schema.yaml"])
    settings = c.validate(raise_exception=True)

    for probe_settings in settings["probes"]:
        if "must" not in probe_settings:
            probe_settings.update({"must": []})
        if "must_not" not in probe_settings:
            probe_settings.update({"must_not": []})
        if "should" not in probe_settings:
            probe_settings.update({"should": []})
    return settings


def set_logging():
    logging.getLogger("paramiko").setLevel(logging.WARNING)
    logging.getLogger("elasticsearch").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.basicConfig(level=logging.DEBUG, datefmt='%H:%M:%S',
                        format='[%(asctime)s] {%(name)10s:%(lineno)3d} %(levelname)8s - %(message)s')


def main():
    set_logging()
    settings = load_settings()
    conn = connect_to_es(settings['settings']['es_host'])

    for probe_settings in settings['probes']:
        stats = get_stats(probe_settings, conn)
        for test in xrange(1, probe_settings["times_to_run"] + 1):
            sample = stats[-test]
            data = stats[:-test]
            std_multiply = probe_settings["std_multiply"]
            print check_anomaly(sample, data, std_multiply)
