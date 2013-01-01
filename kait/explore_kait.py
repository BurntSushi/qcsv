import sys

import numpy as np

import qcsv.kait.qcsv_kait as qcsv

# A convenience function for printing the frequency vector of a column, sorted
# in descending order.
def print_freqs(types, names, rows, colname, limit=25):
    _, _, colcells = qcsv.column(types, names, rows, colname)
    freqs = qcsv.frequencies(colcells)
    desc = sorted(freqs, key=lambda k: freqs[k], reverse=True)
    for value in desc[:limit]:
        print '%d %s' % (freqs[value], qcsv.cell_str(value))

f = "/home/andrew/tmp/kait/chit.csv"
types, names, rows = qcsv.read(f)

# Show our progress.
print 'Table read. Performing analysis.'
print
sys.stdout.flush()

print 'Inspecting browser...'

# Define a function that will put browsers in bins.
def bin_browsers(b):
    b = b.lower()
    bins = ['chrome', 'msie', 'firefox', 'opera', 'safari', '-']
    for bin in bins:
        if bin in b:
            return bin
    return 'other'

# Apply our browser filtering.
rows = qcsv.convert_columns(names, rows, **{'Web Browser': bin_browsers})

# Print the frequency counts for browsers, sorted in descending order.
print_freqs(types, names, rows, 'Web Browser')

print
print 'Inspecting operating system...'

# Now let's explore operating systems. Instead of binning them, let's look at
# the top 25 (after converting to lowercase).
rows = qcsv.convert_columns(names, rows, **{'Operating System': str.lower})
print_freqs(types, names, rows, 'Operating System')

print
print 'Bin operating systems...'

# Now let's attempt to start binning operating systems just like we did web
# browsers. But I'm leaving this as incomplete. The cool thing here is that once
# you bin 'windows', you'll start to see other operating systems bubble up
# the list. (This is supposed to be an iterative process, where you keep on
# adding operating systems to bins.)
def bin_os(os):
    bins = {
        'windows': ['windows'],

        # This is an example of putting a few different kinds of operating
        # systems into one bin. This is a bad example in terms of advertising,
        # but the concept could be useful.
        'apple': ['macintosh', 'ipad', 'iphone'],
    }
    for bin_name in bins:
        for needle in bins[bin_name]:
            if needle in os:
                return bin_name
    return os

rows = qcsv.convert_columns(names, rows, **{'Operating System': bin_os})
print_freqs(types, names, rows, 'Operating System')

