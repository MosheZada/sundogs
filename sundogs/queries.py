from elasticsearch_dsl import Search, Q


def get_count_query(time_window, must_data, must_not_data, should_data, by=None):
    must = [Q("range", **{"@timestamp": {"from": "now-" + time_window, "to": "now"}})]
    must_not = []
    should = []

    for element in must_data:
        must.append(Q("term", **{element["key"]: element["value"]}))

    for element in must_not_data:
        must_not.append(Q("term", **{element["key"]: element["value"]}))

    for element in should_data:
        should.append(Q("term", **{element["key"]: element["value"]}))

    s = Search().query(Q('bool',
                         must=must,
                         must_not=must_not))
    query = s.to_dict()
    if by is not None:
        query.update({"aggs": {
            "by": {
                "terms": {
                    "field": by
                }
            }
        }
        })
    return query


def get_data_histogram_query(interval, time_window, must_data, must_not_data, should_data, value_field="metric",
                             by=None):
    must = [Q("range", **{"@timestamp": {"from": "now-" + time_window, "to": "now"}})]
    must_not = []
    should = []

    for element in must_data:
        must.append(Q("term", **{element["key"]: element["value"]}))

    for element in must_not_data:
        must_not.append(Q("term", **{element["key"]: element["value"]}))

    for element in should_data:
        should.append(Q("term", **{element["key"]: element["value"]}))

    s = Search().query(Q('bool',
                         must=must,
                         must_not=must_not))

    query = s.to_dict()
    date_histogram = {
        "events_by_date": {
            "date_histogram": {
                "field": "@timestamp",
                "interval": interval
            },
            "aggs": {
                "stats_0": {
                    "stats": {
                        "field": value_field
                    }
                }
            }
        }
    }
    if by is not None:
        query.update({"aggs": {
            "events_by": {
                "terms": {
                    "field": by
                },
                "aggs": date_histogram,
            }
        }})
    else:
        query.update({"aggs": date_histogram})
    return query
