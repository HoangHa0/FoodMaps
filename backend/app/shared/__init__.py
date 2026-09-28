"""Contracts between modules.

A module may use another module ONLY through what is defined here; never import another
module's service directly. Changing a file in this package changes an internal API, so the
pull request needs a review from the modules that consume it.
"""
