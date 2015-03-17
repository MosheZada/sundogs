#!/usr/bin/env python
# -*- coding: utf-8 -*-

from math import factorial, pow, sqrt
from scipy.stats import binom, norm
from numpy import nanmean, nanstd


# The alert intends to notify when there is a surprising
# RATE change in current window (normally 30minutes),
# in comparison to the rate previous time window (normally last 24 hours)
def alert_rate_change(training_window_events_count, training_window_positives_count, current_window_count,
                      current_window_positives_count, prob_threshold=0.0001):
    print training_window_events_count, training_window_positives_count, current_window_count, current_window_positives_count
    norm_rate = (training_window_positives_count + 0.0) / training_window_events_count
    curr_rate = (current_window_positives_count + 0.0) / current_window_count
    prob_current = binom.cdf(current_window_positives_count, current_window_count, norm_rate)
    alerting_decision = ((prob_current < prob_threshold) or (prob_current > (1 - prob_threshold)))
    graphing_params = [norm_rate, curr_rate, prob_current, prob_threshold]
    return alerting_decision, graphing_params


# The alert intends to notify when there is a surprising
# COUNT change in current window (normally 30minutes),
# in comparison to previous time window (normally last 24 hours)
def alert_count_change(training_window_size_in_ms, training_window_positives_count, current_window_size_in_ms,
                       current_window_positives_count,
                       prob_threshold=0.0001):
    return alert_rate_change(training_window_size_in_ms, training_window_positives_count, current_window_size_in_ms,
                             current_window_positives_count,
                             prob_threshold)


# The alert intends to notify when there is a surprising
# MEAN change in current window (normally 30minutes),
# in comparison to previous time window (normally last 24 hours)
# This Assumes NORMAL dist of values
def alert_mean_change(training_window_vals, current_window_vals, prob_threshold=0.0001):
    mean_norm_win = nanmean(training_window_vals)
    std_mean_norm_win = nanstd(training_window_vals) / sqrt(
        len(training_window_vals))  # assuming small fraction of nans
    mean_curr_win = nanmean(current_window_vals)
    std_mean_curr_win = nanstd(current_window_vals) / sqrt(len(current_window_vals))  # assuming small fraction of nans
    overall_std = sqrt(std_mean_curr_win * std_mean_curr_win + std_mean_norm_win * std_mean_norm_win)
    prob_current_mean = norm.cdf(mean_curr_win, mean_norm_win, overall_std)
    alerting_decision = ((prob_current_mean < prob_threshold) or (prob_current_mean > (1 - prob_threshold)))
    graphing_params = [mean_norm_win, mean_curr_win, std_mean_norm_win, std_mean_curr_win, prob_threshold]
    return alerting_decision, graphing_params
