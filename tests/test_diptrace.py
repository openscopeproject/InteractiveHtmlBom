import logging
from types import SimpleNamespace

from InteractiveHtmlBom.ecad import get_parser_by_extension


SAMPLE = '''<?xml version="1.0" encoding="UTF-8"?>
<Source Type="DipTrace-PCB" Version="5.0" Units="mm">
  <Library Type="DipTrace-ComponentLibrary" Units="mm">
    <Library Type="DipTrace-PatternLibrary" Units="mm">
      <PadStyles><PadStyle Name="THT" Type="Through" HoleType="Round" Hole="0.8">
        <MainStack Shape="Round" Width="1.6" Height="1.6"/>
      </PadStyle></PadStyles>
      <Patterns><Pattern PatternStyle="DIP-2" Id="0" Mounting="Through" Width="5" Height="3">
        <Name>DIP-2</Name><Pads>
          <Pad Id="1" Style="THT" X="-1.27" Y="0" Angle="0" Side="Top"><Number>1</Number></Pad>
          <Pad Id="2" Style="THT" X="1.27" Y="0" Angle="0" Side="Top"><Number>2</Number></Pad>
        </Pads><Shapes><Shape Id="0" Type="Line" Layer="Top Silk" LineWidth="0.2">
          <Points><Point X="-2" Y="-1"/><Point X="2" Y="-1"/></Points>
        </Shape></Shapes>
      </Pattern></Patterns>
    </Library>
  </Library>
  <Board><CopperLayers><Lay Id="0" Type="Signal"><Name>Top</Name></Lay></CopperLayers>
    <BoardOutline><Points><Point X="0" Y="0"/><Point X="10" Y="0"/><Point X="10" Y="8"/><Point X="0" Y="8"/></Points></BoardOutline>
    <Components><Component Id="0" PatternStyle="DIP-2" X="3" Y="4" Angle="0" Side="Top">
      <RefDes>U1</RefDes><Value>TEST</Value><Pads><Pad Id="1" NetId="0"/><Pad Id="2" NetId="-1"/></Pads>
    </Component></Components>
    <Nets><Net Id="0"><Name>GND</Name><Traces><Trace Id="0"><Points>
      <Point Id="0" X="3" Y="4" Lay="0" Width="0.3"/><Point Id="1" X="5" Y="4" Lay="0" Width="0.3"/>
    </Points></Trace></Traces></Net></Nets>
    <CopperPours><CopperPour Id="0" NetId="0" Lay="0"><Points>
      <Point X="1" Y="1"/><Point X="2" Y="1"/><Point X="2" Y="2"/>
    </Points></CopperPour></CopperPours>
  </Board>
</Source>'''


def config():
    return SimpleNamespace(include_tracks=True, include_nets=True)


def test_diptrace_parser_reads_board(tmp_path):
    file_name = tmp_path / 'board.dip'
    file_name.write_text(SAMPLE, encoding='utf-8')
    parser = get_parser_by_extension(str(file_name), config(), logging.getLogger(__name__))
    pcbdata, components = parser.parse()

    assert components[0].ref == 'U1'
    assert pcbdata['edges_bbox'] == {'minx': -0.05, 'miny': -0.05, 'maxx': 10.05, 'maxy': 8.05}
    assert pcbdata['footprints'][0]['pads'][0]['type'] == 'th'
    assert pcbdata['footprints'][0]['pads'][0]['net'] == 'GND'
    assert len(pcbdata['drawings']['silkscreen']['F']) == 1
    assert len(pcbdata['tracks']['F']) == 1
    assert len(pcbdata['zones']['F']) == 1


def test_diptrace_mil_units_are_normalized(tmp_path):
    file_name = tmp_path / 'board.dipxml'
    file_name.write_text(SAMPLE.replace('Units="mm"', 'Units="mil"').replace('X="10"', 'X="393.7008"').replace('Y="8"', 'Y="314.9606"'), encoding='utf-8')
    parser = get_parser_by_extension(str(file_name), config(), logging.getLogger(__name__))
    pcbdata, _ = parser.parse()
    assert round(pcbdata['edges_bbox']['maxx'], 2) == 10.0
