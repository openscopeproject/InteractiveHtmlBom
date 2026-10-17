import argparse
import ast
import itertools
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from InteractiveHtmlBom.core.config import Config
from InteractiveHtmlBom.core.ibom import skip_component
from InteractiveHtmlBom.ecad.common import Component


class FilterExcludedTests(unittest.TestCase):
    FLAGS = {
        '--filter-excluded': False,
        '--no-filter-excluded': True,
        '--blacklist-virtual': False,
        '--no-blacklist-virtual': True,
    }

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.config = Config('test', self.directory.name)
        self.parser = argparse.ArgumentParser()
        Config.add_options(self.parser, 'test')

    def test_default_still_filters_excluded_components(self):
        args = self.parser.parse_args([])
        self.assertFalse(args.no_blacklist_virtual)
        self.config.set_from_args(args)
        self.assertTrue(self.config.blacklist_virtual)

    def test_new_and_deprecated_flags_share_last_option_precedence(self):
        for length in range(1, 4):
            for flags in itertools.product(self.FLAGS, repeat=length):
                with self.subTest(flags=flags):
                    args = self.parser.parse_args(flags)
                    disabled = self.FLAGS[flags[-1]]
                    self.assertEqual(args.no_blacklist_virtual, disabled)
                    self.config.set_from_args(args)
                    self.assertEqual(self.config.blacklist_virtual,
                                     not disabled)

    def test_legacy_ini_default_and_cli_overrides(self):
        ini_path = Path(self.config.local_config_file)
        for enabled in (True, False):
            ini_path.write_text('[general]\nblacklist_virtual=%s\n' %
                                enabled, encoding='utf-8')
            defaults = self.config.get_ini_defaults()
            self.assertEqual(defaults['no_blacklist_virtual'], not enabled)
            self.parser.set_defaults(**defaults)
            args = self.parser.parse_args(['--use-ini'])
            self.config.set_from_args(args)
            self.assertEqual(self.config.blacklist_virtual, enabled)
            for flag, disabled in self.FLAGS.items():
                with self.subTest(enabled=enabled, flag=flag):
                    args = self.parser.parse_args(['--use-ini', flag])
                    self.config.set_from_args(args)
                    self.assertEqual(self.config.blacklist_virtual,
                                     not disabled)

    def test_missing_ini_setting_keeps_filtering_default(self):
        Path(self.config.local_config_file).write_text(
            '[general]\n', encoding='utf-8')
        self.parser.set_defaults(**self.config.get_ini_defaults())
        self.config.set_from_args(self.parser.parse_args(['--use-ini']))
        self.assertTrue(self.config.blacklist_virtual)

    def test_component_filtering_is_unchanged(self):
        for flags in ([], *([flag] for flag in self.FLAGS)):
            self.config.set_from_args(self.parser.parse_args(flags))
            for attr in ('Virtual', 'Normal', 'Unspecified', None):
                with self.subTest(flags=flags, attr=attr):
                    component = Component('R1', '1k', 'R', 'F', attr)
                    self.assertEqual(skip_component(component, self.config),
                                     self.config.blacklist_virtual and
                                     attr == 'Virtual')

    def test_help_describes_new_flags_and_deprecates_old_flags(self):
        actions = self.parser._option_string_actions
        for flag in ('--filter-excluded', '--no-filter-excluded'):
            help_text = actions[flag].help
            self.assertIn("'Exclude from BOM'", help_text)
            self.assertIn('older KiCad versions and other parsers', help_text)
            self.assertIn("'Virtual' attribute", help_text)
        for old, new in (('--blacklist-virtual', '--filter-excluded'),
                         ('--no-blacklist-virtual', '--no-filter-excluded')):
            self.assertIn('(Deprecated)', actions[old].help)
            self.assertIn(new, actions[old].help)
        rendered_help = self.parser.format_help()
        for flag in self.FLAGS:
            self.assertIn(flag, rendered_help)

    def test_dialog_label_and_tooltip_match_formbuilder(self):
        root = Path(__file__).resolve().parents[1]
        fbp = ET.parse(root / 'settings_dialog.fbp')
        controls = [
            obj for obj in fbp.iter('object')
            if obj.get('class') == 'wxCheckBox' and
            obj.findtext("property[@name='name']") ==
            'blacklistVirtualCheckbox'
        ]
        self.assertEqual(len(controls), 1)
        control = controls[0]
        label = control.findtext("property[@name='label']")
        tooltip = control.findtext("property[@name='tooltip']")
        self.assertEqual(label, 'Filter excluded components')
        self.assertEqual(control.findtext("property[@name='checked']"), '1')
        self.assertIn('older KiCad versions and other parsers', tooltip)
        self.assertIn("'Virtual' attribute", tooltip)
        self.assertIn("Previously called 'Blacklist virtual components'",
                      tooltip)
        self.assertIn("'Unspecified' footprint type alone is not excluded",
                      tooltip)

        dialog = ast.parse((root / 'InteractiveHtmlBom/dialog/dialog_base.py')
                           .read_text(encoding='utf-8'))
        calls = [
            node for node in ast.walk(dialog)
            if isinstance(node, ast.Call) and
            isinstance(node.func, ast.Attribute) and
            isinstance(node.func.value, ast.Attribute) and
            node.func.value.attr == 'blacklistVirtualCheckbox'
        ]
        tooltips = [node for node in calls if node.func.attr == 'SetToolTip']
        values = [node for node in calls if node.func.attr == 'SetValue']
        self.assertEqual(len(tooltips), 1)
        self.assertEqual(ast.literal_eval(tooltips[0].args[0]), tooltip)
        self.assertEqual(len(values), 1)
        self.assertTrue(ast.literal_eval(values[0].args[0]))
        assignments = [
            node for node in ast.walk(dialog)
            if isinstance(node, ast.Assign) and
            any(isinstance(target, ast.Attribute) and
                target.attr == 'blacklistVirtualCheckbox'
                for target in node.targets)
        ]
        self.assertEqual(len(assignments), 1)
        self.assertEqual(ast.literal_eval(assignments[0].value.args[2]), label)


if __name__ == '__main__':
    unittest.main()
