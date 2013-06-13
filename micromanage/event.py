#!/usr/bin/env python3
# micromanage event bus.

handlers = {}

def emit(type, *args, **kwargs):
    if type in handlers:
        for handler in handlers[type]:
            handler(*args, **kwargs)

def add_handler(type, handler):
    if type not in handlers:
        handlers[type] = []
    handlers[type].append(handler)
