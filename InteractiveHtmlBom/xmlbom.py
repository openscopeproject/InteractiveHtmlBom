from xml.dom import minidom

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def getPartNumbers(filename, fieldName = "Part Number"):
    pairs = {}
    try:
        xmldoc = minidom.parse(filename)
        components = xmldoc.getElementsByTagName('comp')
        for c in components:
            fields = c.getElementsByTagName('field')
            for f in fields:
                pairs[c.attributes['ref'].value] = getText(f.childNodes)
    except:
        print 'No XML file found. Generate XML BOM from EESCHEMA'
        return {}
    return pairs
