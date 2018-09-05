from xml.dom import minidom
from os import path
def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def getPartNumbers(filename, fieldName):
    pairs = {}
    if not path.isfile(filename):
        print 'No XML file found. Part numbers will not be displayed. Generate XML BOM from EESCHEMA'
        return {}
    try:
        xmldoc = minidom.parse(filename)
        components = xmldoc.getElementsByTagName('comp')
        for c in components:
            fields = c.getElementsByTagName('field')
            for f in fields:
                if f.attributes['name'].value == fieldName:
                    pairs[c.attributes['ref'].value] = getText(f.childNodes)
    except:
        print 'XML Parse error'
        return {}
    # print pairs
    return pairs
