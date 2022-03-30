from lxml import etree


def getXmlValue(root, idName, default):
    """
    Return an xml value identifed by idName.
    :param root:  root where we search idName:
    :param idName: idName string to find:
    :param default: default value to return if not find:
    :return value if find otherwise return default:
    """
    try:
        dataRet = root.find(idName).text
    except:
        return default
    else:
        return dataRet


def getPosFromXml(root):
    """
    Read postion form xml file.
    :param root:
    :return:Return a disct like {'X': 1.0, 'Y': 1.0, 'Z': 1.0}
    """
    return {'X': float(getXmlValue(root, 'X', 0.0)), 'Y': float(getXmlValue(root, 'Y', 0.0)),
            'Z': float(getXmlValue(root, 'Z', 0.0))}


def addPosToXml(root, rootName, xPos, yPos, zPos):
    """
    Add position to Xml
    :param root:
    :param rootName:
    :param xPos:
    :param yPos:
    :param zPos:
    :return: nothing
    """
    posRoot = etree.SubElement(root, rootName)
    etree.SubElement(posRoot, 'X').text = str(xPos)
    etree.SubElement(posRoot, 'Y').text = str(yPos)
    etree.SubElement(posRoot, 'Z').text = str(zPos)
