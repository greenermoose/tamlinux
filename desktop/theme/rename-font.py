#!/usr/bin/env python3
"""Rename inherited font identity without changing any glyph table."""
import sys
from fontTools.ttLib import TTFont
source, destination = sys.argv[1:]
font = TTFont(source, recalcTimestamp=False)
# Family, unique ID, full name, PostScript name, typographic family and WWS.
identities = {1: 'Tamlinux Icons', 3: 'Tamlinux Icons Regular 1.0',
              4: 'Tamlinux Icons Regular', 6: 'TamlinuxIcons-Regular',
              16: 'Tamlinux Icons', 21: 'Tamlinux Icons'}
for record in font['name'].names:
    if record.nameID in identities:
        record.string = identities[record.nameID].encode(record.getEncoding())
font.save(destination)
result = TTFont(destination, recalcTimestamp=False)
for table in ('cmap', 'glyf', 'hmtx'):
    assert font[table].compile(font) == result[table].compile(result), table
for record in result['name'].names:
    if record.nameID in identities:
        assert 'omarchy' not in record.toUnicode().lower()
print('Tamlinux Icons: names replaced; cmap/glyf/hmtx preserved')
