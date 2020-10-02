import os
import sys
from datetime import datetime
import csv
import sqlite3

from .common import EcadParser, Component

PY3 = sys.version_info[0] == 3

if PY3:
    string_types = str
else:
    string_types = basestring


class GenericCentroidParser(EcadParser):
    ''' Generic centroid file parser '''

    def __init__(self,
                 file_name,
                 config,
                 logger,
                 width=0.,
                 height=0.,
                 mpp=25.4 / 600):
        # type: (GenericCentroidParser, str, Config, float, float, float)

        EcadParser.__init__(self, file_name, config, logger)
        self.width = width
        self.height = height
        self.mpp = mpp
        self.bbox_size = 0.1 * 25.4 / self.mpp

        self.components = None
        self.modules = None
        self.silkscreen = None
        self.bom = None

        self.conn = None

    def parse_xy(self):
        ''' Parse the centroid file '''

        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row

        self.conn.execute('''CREATE TABLE xy(refdes STRING PRIMARY KEY,
               x FLOAT, y FLOAT, angle FLOAT, side STRING)''')
        self.conn.execute('''CREATE TABLE bom(refdes STRING PRIMARY KEY,
               footprint STRING, value STRING, side STRING)''')

        self.conn.commit()

        with open(self.file_name, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                # Skip all comments
                if row[0][0] == '#':
                    continue

                # Parse cells
                refdes = row[0]
                description = row[1]
                value = row[2]
                rotation = float(row[5])
                coord_x = float(row[3]) / self.mpp

                if row[6] == 'top':
                    top_or_bottom = 'F'
                    # Centroid file coordinates' origin is at bottom-left,
                    # but raster images have origin at top-left.
                    coord_y = (self.height - float(row[4])) / self.mpp
                else:
                    top_or_bottom = 'B'
                    coord_y = float(row[4]) / self.mpp
                    # Assuming the back-side PCB rendering is vertically flipped,
                    # so no need to flip here.

                # Append to in-memory database
                self.conn.execute('INSERT INTO bom VALUES (?,?,?,?)',
                                  (refdes, description, value, top_or_bottom))

                self.conn.execute(
                    'INSERT INTO xy VALUES (?,?,?,?,?)',
                    (refdes, coord_x, coord_y, rotation, top_or_bottom))

            self.conn.commit()

    def get_bom(self):
        ''' Create the bill of materials. '''
        self.bom = {'B': [], 'F': [], 'both': [], 'skipped': []}

        for row in self.conn.execute(
                '''SELECT footprint, value, side, count(*) AS qty FROM bom
                   GROUP BY side, footprint, value'''):
            bom_group = [
                row['qty'],
                str(row['value']),
                str(row['footprint']),
                [[str(r['refdes']), r['id']] for r in self.conn.execute(
                    '''SELECT bom.refdes, xy.rowid - 1 AS id FROM bom, xy
                     WHERE bom.refdes = xy.refdes AND
                     footprint=? AND value=?''', (row['footprint'],
                                                  row['value']))], []
            ]

            self.bom['both'].append(bom_group)
            self.bom[row['side']].append(bom_group)

    def get_components(self):
        ''' Create a list of components '''
        self.components = []

        for row in self.conn.execute(
                'SELECT refdes, footprint, value, side FROM bom'):
            self.components.append(
                Component(row['refdes'], str(row['value']),
                          str(row['footprint']), str(row['side'])))

    def get_modules(self):
        ''' Create a list of modules. '''
        self.modules = []

        for row in self.conn.execute('SELECT refdes, x, y, side FROM xy'):
            self.modules.append({
                'center': [row['x'], row['y']],
                'bbox': {
                    'angle': 0,
                    'pos': [row['x'], row['y']],
                    'relpos': [self.bbox_size * -0.5, self.bbox_size * -0.5],
                    'size': [self.bbox_size, self.bbox_size],
                },
                'pads': [],
                'drawings': [],
                'layer': row['side'],
                'ref': str(row['refdes']),
            })

    def get_background(self):
        ''' Create the link to the photorealistic rendering of PCBs in the background. '''
        self.silkscreen = dict(F=[], B=[])

        prefix = os.path.splitext(self.file_name)[0]

        self.silkscreen['F'].append({
            'start': [0, 0],
            'type': 'url',
            'url': prefix + '-front.png'
        })

        self.silkscreen['B'].append({
            'start': [0, 0],
            'type': 'url',
            'url': prefix + '-back.png'
        })

    def parse(self):
        ''' Parse the centroid file and return the pcbdata and components '''

        self.get_background()
        self.parse_xy()
        if self.width <= 0 or self.height <= 0:
            self.logger.warn(
                'Missing PCB dimensions in millimeter. Component positions will be inaccurate.'
            )

        self.get_bom()
        self.get_modules()

        title = os.path.basename(self.file_name)
        date = datetime.fromtimestamp(os.path.getmtime(
            self.file_name)).strftime('%Y-%m-%d')

        pcbdata = {
            'edges_bbox': {
                'minx': 0,
                'miny': 0,
                'maxx': self.width / self.mpp,
                'maxy': self.height / self.mpp
            },
            'edges': [],
            'silkscreen': self.silkscreen,
            'fabrication': {
                'F': [],
                'B': [],
            },
            'modules': self.modules,
            'metadata': {
                'title': title,
                'company': '',
                'revision': '',
                'date': date
            },
            'bom': self.bom,
            'font_data': {}
        }

        self.get_components()

        return pcbdata, self.components
