import io
import os
import sys

from .common import EcadParser, Component, BoundingBox, ExtraFieldData
from ..core.fontparser import FontParser


class AltiumDesignerParser(EcadParser):
    TOP_COPPER_LAYER = 1
    BOT_COPPER_LAYER = 2
    TOP_SILK_LAYER = 3
    BOT_SILK_LAYER = 4
    TOP_ASSEMBLY_LAYER = 13
    BOT_ASSEMBLY_LAYER = 14

    def get_altiumdesigner_pcb(self):
        import json
        with io.open(self.file_name, 'r', encoding='utf-8') as f:
            return json.load(f)

    def parse_board(self, board):
        edges = []

        for item in board:
            if item['Type'] == 'segment':
                segment = {
                    'end': [item['X2'], item['Y2']],
                    'start': [item['X1'], item['Y1']],
                    'type': 'segment',
                    'width': item['Width'],
                }
                edges.append(segment)

            if item['Type'] == 'arc':
                arc = {
                    'start': [item['X'], item['Y']],
                    'endangle': item['Angle2'],
                    'width': item['Width'],
                    'radius': item['Radius'],
                    'startangle': item['Angle1'],
                    'type': 'arc',
                }
                edges.append(arc)

        return edges

    def parse_pad(self, data):
        layers = []
        if data['Layer'] == 'TopLayer':
            layers = ['F']
        if data['Layer'] == 'BottomLayer':
            layers = ['B']
        if data['Layer'] == 'MultiLayer':
            layers = ['F', 'B']

        pad = {
            'angle': data['Angle'],
            'layers': layers,
            'pos': [data['X'], data['Y']],
            'shape': data['Shape'],
            'size': [data['Width'], data['Height']],
            'type': data['Type'],
        }

        if data['Type'] == 'th':
            pad['drillshape'] = data['DrillShape']
            pad['drillsize'] = [data['DrillWidth'], data['DrillHeight']]

        if data['Pin1']:
            pad['pin1'] = True

        if self.config.include_nets:
            pad['net'] = data['Net']

        return pad, data['Net']

    def parse_pads(self, data):
        pads = []
        nets = []

        for item in data:
            pad, net = self.parse_pad(item)

            pads.append(pad)
            nets.append(net)

        return pads, nets

    def parse_footprint(self, data, settings):
        layer = ''
        if data['Layer'] == 'TopLayer':
            layer = 'F'
        if data['Layer'] == 'BottomLayer':
            layer = 'B'

        bbox = {
            'angle': 0,
            'pos': [data['X'], data['Y']],
            'relpos': [0, 0],
            'size': [data['Width'], data['Height']],
        }

        pads, nets = self.parse_pads(data['Pads'])

        footprint = {
            'bbox': bbox,
            'drawings':  [],
            'layer': layer,
            'pads': pads,
            'ref': data['Designator']
        }

        extra = dict(zip(settings['Fields'], data['Fields']))

        component = Component(data['Designator'], data['Value'], data['Footprint'], layer, extra_fields=extra)

        return footprint, component, nets

    def parse_data(self, data, settings):
        footprints = []
        components = []
        nets = []

        for item in data:
            footprint, component, footprint_nets = self.parse_footprint(item, settings)

            footprints.append(footprint)
            components.append(component)
            
            nets += footprint_nets

        return footprints, components, nets

    def parse_extra(self, extra):
        drawings = {}
        tracks = {}
        zones = {}
        font_data = {}
        nets = []

        font_parser = FontParser()

        for item in extra:
            if item['Type'] == 'segment':
                segment = {
                    'end': [item['X2'], item['Y2']],
                    'start': [item['X1'], item['Y1']],
                    'type': 'segment',
                    'width': item['Width'],
                }

                if self.config.include_nets:
                    segment['net'] = item['Net']

                nets.append(item['Net'])

                if item['Layer'] == 'TopOverlay':
                    drawings.setdefault(self.TOP_SILK_LAYER, []).append(segment)
                if item['Layer'] == 'BottomOverlay':
                    drawings.setdefault(self.BOT_SILK_LAYER, []).append(segment)
                if item['Layer'] == 'TopLayer':
                    tracks.setdefault(self.TOP_COPPER_LAYER, []).append(segment)
                if item['Layer'] == 'BottomLayer':
                    tracks.setdefault(self.BOT_COPPER_LAYER, []).append(segment)

            if item['Type'] == 'via':
                via = {
                    'end': [item['X'], item['Y']],
                    'start': [item['X'], item['Y']],
                    'type': 'segment',
                    'width': item['Width'],
                    'drillsize': item['DrillWidth'],
                }

                if self.config.include_nets:
                    via['net'] = item['Net']

                nets.append(item['Net'])

                if item['Layer'] == 'TopLayer':
                    tracks.setdefault(self.TOP_COPPER_LAYER, []).append(via)
                if item['Layer'] == 'BottomLayer':
                    tracks.setdefault(self.BOT_COPPER_LAYER, []).append(via)
                if item['Layer'] == 'MultiLayer':
                    tracks.setdefault(self.TOP_COPPER_LAYER, []).append(via)
                    tracks.setdefault(self.BOT_COPPER_LAYER, []).append(via)

            if item['Type'] == 'arc':
                arc = {
                    'start': [item['X'], item['Y']],
                    'endangle': item['Angle2'],
                    'width': item['Width'],
                    'radius': item['Radius'],
                    'startangle': item['Angle1'],
                    'type': 'arc',
                }

                if item['Layer'] == 'TopOverlay':
                    drawings.setdefault(self.TOP_SILK_LAYER, []).append(arc)
                if item['Layer'] == 'BottomOverlay':
                    drawings.setdefault(self.BOT_SILK_LAYER, []).append(arc)

            if item['Type'] == 'text':
                text = {
                    'angle': item['Angle'],
                    'attr': [],
                    'height': item['Height'],
                    'justify': [0, 0],
                    'pos': [item['X'], item['Y']],
                    'text': item['Text'],
                    'thickness': 0.15,
                    'width': item['Width'],
                }

                if item['Mirrored']:
                    text['attr'].append('mirrored')
                if item['Designator']:
                    text['ref'] = 1
                if item['Value']:
                    text['val'] = 1

                font_parser.parse_font_for_string(item['Text'])

                if item['Layer'] == 'TopOverlay':
                    drawings.setdefault(self.TOP_SILK_LAYER, []).append(text)
                if item['Layer'] == 'BottomOverlay':
                    drawings.setdefault(self.BOT_SILK_LAYER, []).append(text)

            if item['Type'] == 'polygon':
                polygon = {
                    'type': 'polygon',
                    'angle': 0,
                    'pos': [0, 0],
                    'polygons': item['EX'],
                }

                if self.config.include_nets:
                    polygon['net'] = item['Net']

                nets.append(item['Net'])

                if item['Layer'] == 'TopOverlay':
                    drawings.setdefault(self.TOP_SILK_LAYER, []).append(polygon)
                if item['Layer'] == 'BottomOverlay':
                    drawings.setdefault(self.BOT_SILK_LAYER, []).append(polygon)
                if item['Layer'] == 'TopLayer':
                    zones.setdefault(self.TOP_COPPER_LAYER, []).append(polygon)
                if item['Layer'] == 'BottomLayer':
                    zones.setdefault(self.BOT_COPPER_LAYER, []).append(polygon)

        for (c, wl) in font_parser.get_parsed_font().items():
            if c not in font_data:
                font_data[c] = wl

        return drawings, tracks, zones, font_data, nets

    def get_edges_bbox(self, pcb):
        return {
            'maxx': pcb['BB']['X2'],
            'maxy': pcb['BB']['Y2'],
            'minx': pcb['BB']['X1'],
            'miny': pcb['BB']['Y1'],
        }

    def get_metadata(self, pcb):
        return {
            'title': pcb['Metadata']['Title'],
            'revision': pcb['Metadata']['Revision'],
            'company': pcb['Metadata']['Company'],
            'date': pcb['Metadata']['Date'],
        }

    def parse(self):
        pcb = self.get_altiumdesigner_pcb()

        edges = self.parse_board(pcb['Board'])

        footprints, components, data_nets = self.parse_data(pcb['Data'], pcb['Settings'])

        drawings, tracks, zones, font_data, extra_nets = self.parse_extra(pcb['Extra'])

        pcbdata = {
            'edges_bbox': self.get_edges_bbox(pcb),
            'edges': edges,
            'drawings': {
                'silkscreen': {
                    'F': drawings.get(self.TOP_SILK_LAYER, []),
                    'B': drawings.get(self.BOT_SILK_LAYER, []),
                },
                'fabrication': {
                    'F': drawings.get(self.TOP_ASSEMBLY_LAYER, []),
                    'B': drawings.get(self.BOT_ASSEMBLY_LAYER, []),
                },
            },
            'footprints': footprints,
            'metadata': self.get_metadata(pcb),
            'bom': {},
            'font_data': font_data
        }

        if self.config.include_nets:
            nets = ['No Net']
            nets = list(set(nets + data_nets + extra_nets))
            pcbdata['nets'] = nets

        if self.config.include_tracks:
            def filter_tracks(drawing_list, drawing_type, keys):
                result = []
                for d in drawing_list:
                    if d['type'] == drawing_type:
                        r = {}
                        for key in keys:
                            if key in d.keys():
                                r[key] = d[key]
                        result.append(r)
                return result

            pcbdata['tracks'] = {
                'F': filter_tracks(tracks.get(self.TOP_COPPER_LAYER, []),
                                   'segment', ['start', 'end', 'width', 'drillsize', 'net']),
                'B': filter_tracks(tracks.get(self.BOT_COPPER_LAYER, []),
                                   'segment', ['start', 'end', 'width', 'drillsize', 'net']),
            }
            pcbdata['zones'] = {
                'F': filter_tracks(zones.get(self.TOP_COPPER_LAYER, []),
                                   'polygon', ['polygons', 'net']),
                'B': filter_tracks(zones.get(self.BOT_COPPER_LAYER, []),
                                   'polygon', ["polygons", 'net']),
            }

        return pcbdata, components
