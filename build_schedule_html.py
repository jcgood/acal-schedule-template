#!/usr/bin/env python3
"""Entry point: build and publish the conference schedule.

Usage:
    .venv/bin/python3 build_schedule_html.py [--output schedule.html]

All logic lives in schedule/build.py. This file stays thin so that
schedule/ can be imported as a package by conf.py or other tools.
"""
from schedule.build import build

if __name__ == '__main__':
    build()
