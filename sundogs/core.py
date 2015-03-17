#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import queries
import logics

from pykwalify.core import Core
from elasticsearch import Elasticsearch


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
    logging.getLogger("pykwalify").setLevel(logging.WARNING)
    logging.basicConfig(level=logging.DEBUG, datefmt='%H:%M:%S',
                        format='[%(asctime)s] {%(name)10s:%(lineno)3d} %(levelname)8s - %(message)s')


def query(conn, settings, window, must):
    return conn.search(index="_all",
                       search_type="count",
                       body=queries.get_count_query(window,
                                                    must,
                                                    settings["must_not"],
                                                    settings["should"]))["hits"]["total"]


def main():
    set_logging()
    settings = load_settings()
    conn = Elasticsearch(settings['settings']['es_host'])
    assert conn.ping(), "Cannot connect to ES host"
    for probe_settings in settings['probes']:
        if probe_settings["type"] == "rate":
            training_window_events_count = query(conn, probe_settings, probe_settings["norm_window"],
                                                 probe_settings["must"])
            training_window_positives_count = query(conn, probe_settings, probe_settings["norm_window"],
                                                    probe_settings["must"] + probe_settings["positive"])
            current_window_count = query(conn, probe_settings, probe_settings["current_window"], probe_settings["must"])
            current_window_positives_count = query(conn, probe_settings, probe_settings["current_window"],
                                                   probe_settings["must"] + probe_settings["positive"])
            training_window_events_count -= current_window_count
            training_window_positives_count -= current_window_positives_count
            print logics.alert_rate_change(training_window_events_count, training_window_positives_count,
                                           current_window_count,
                                           current_window_positives_count)

