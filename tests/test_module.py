import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest


def test_module_import():
    import InteractiveHtmlBom  # noqa


@pytest.mark.parametrize('args, expected', [([], False), (['--highlight-row-on-click'], True)])
def test_cli_highlight_row_on_click(tmp_path, args, expected):
    board = tmp_path / 'board.json'
    board.write_text(json.dumps({
        'spec_version': 1,
        'pcbdata': {
            'edges_bbox': {'minx': 0, 'miny': 0, 'maxx': 10, 'maxy': 10},
            'edges': [],
            'drawings': {},
            'footprints': [],
            'metadata': {'title': '', 'revision': '', 'company': '', 'date': ''},
        },
        'components': [],
    }), encoding='utf-8')

    generator = (Path(__file__).resolve().parents[1] /
                 'InteractiveHtmlBom/generate_interactive_bom.py')
    result = subprocess.run(
        [sys.executable, str(generator), str(board), '--no-browser', *args],
        env=dict(os.environ, INTERACTIVE_HTML_BOM_NO_DISPLAY='1'),
        capture_output=True, text=True, timeout=90,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    html = (tmp_path / 'bom' / 'ibom.html').read_text(encoding='utf-8')
    match = re.search(r'^var config = (.+)$', html, re.M)
    assert match is not None
    assert json.loads(match.group(1)).get('highlight_row_on_click', False) is expected
