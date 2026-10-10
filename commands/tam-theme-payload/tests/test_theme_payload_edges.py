"""Regression coverage for parser and numeric limits."""
from tests import test_theme_payload as helpers
import unittest


class ThemePayloadEdges(unittest.TestCase):
    setUp = helpers.ThemePayload.setUp
    write = helpers.ThemePayload.write
    theme = helpers.ThemePayload.theme
    override = helpers.ThemePayload.override
    write_theme = helpers.ThemePayload.write_theme
    write_override = helpers.ThemePayload.write_override
    run_cli = helpers.ThemePayload.run_cli
    payload = helpers.ThemePayload.payload
    assertPayload = helpers.ThemePayload.assertPayload

    def test_huge_style_integers_are_omitted_without_losing_surfaces(self):
        for number in ('9' * 400, '-' + '9' * 400):
            with self.subTest(number=number[:12]):
                self.write_theme(colors=helpers.COLORS, shell=
                                 '[menu]\nbackground = "#123456"\n'
                                 '[font]\nbase-size = ' + number + '\n'
                                 '[spacing]\nscale = ' + number + '\n')
                self.assertPayload({'palette': helpers.PALETTE,
                                    'surfaces': {'menu.background': '#123456'},
                                    'style': {}})

    def test_huge_alpha_integers_clamp_before_float_conversion(self):
        for number, color in [('9' * 400, '#123456'),
                              ('-' + '9' * 400, '#00123456')]:
            with self.subTest(number=number[:12]):
                self.write_theme(colors=helpers.COLORS, shell=
                                 '[menu]\nbackground = "#123456"\n'
                                 'background-alpha = ' + number + '\n')
                self.assertPayload({'palette': helpers.PALETTE,
                                    'surfaces': {'menu.background': color}, 'style': {}})

    def test_parser_limits_discard_only_the_affected_input_file(self):
        for body in ('unused = ' + '9' * 5000 + '\n',
                     'unused = ' + '[' * 1500 + '0' + ']' * 1500 + '\n'):
            with self.subTest(body=body[:20]):
                self.write_theme(colors=helpers.COLORS, shell=body)
                self.write_override('[font]\nbase-size = 11\n')
                self.assertPayload({'palette': helpers.PALETTE, 'surfaces': {},
                                    'style': {'fontBaseSize': 11}})
                self.write_theme(colors=body, shell='[menu]\nbackground = "#123456"\n')
                self.assertPayload({'palette': helpers.DEFAULTS,
                                    'surfaces': {'menu.background': '#123456'},
                                    'style': {'fontBaseSize': 11}})
                self.write_theme(colors=helpers.COLORS)
                self.write_override(body)
                self.assertPayload({'palette': helpers.PALETTE,
                                    'surfaces': {'menu.background': '#123456'}, 'style': {}})
