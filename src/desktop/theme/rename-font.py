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
# The source also has a PostScript glyph alias carrying the old software name.
# Change its exported alias, while leaving glyph order, outlines and codepoints
# intact. Unused aliases are otherwise serialized by FontTools too.
if font['post'].formatType == 2.0:
    post = font['post']
    post.extraNames = [name for name in post.extraNames if 'omarchy' not in name.lower()]
    for glyph in font.getGlyphOrder():
        if 'omarchy' in glyph.lower():
            post.mapping[glyph] = glyph.lower().replace('omarchy', 'tamlinux')
font.save(destination)
result = TTFont(destination, recalcTimestamp=False)
for table in ('cmap', 'glyf', 'hmtx'):
    assert font[table].compile(font) == result[table].compile(result), table
for record in result['name'].names:
    if record.nameID in identities:
        assert 'omarchy' not in record.toUnicode().lower()
assert not any('omarchy' in name.lower() for name in result.getGlyphOrder())
print('Tamlinux Icons: names replaced; cmap/glyf/hmtx preserved')
