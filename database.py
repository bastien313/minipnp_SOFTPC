from lxml import etree
import Board as brr
import xmledit as xe


class Model:
    def __init__(self, dicConf):
        self.name = dicConf['NAME'] if 'NAME' in dicConf else ' '
        self.width = dicConf['WIDTH'] if 'WIDTH' in dicConf else 1.0
        self.length = dicConf['LENGTH'] if 'LENGTH' in dicConf else 1.0
        self.height = dicConf['HEIGHT'] if 'HEIGHT' in dicConf else 1.0
        self.scanHeight = dicConf['SCAN_HEIGHT'] if 'SCAN_HEIGHT' in dicConf else 0.5
        self.aliasList = dicConf['ALIAS'] if 'ALIAS' in dicConf else ''
        self.pickupSpeed = dicConf['PISPE'] if 'PISPE' in dicConf else 20.0
        self.placeSpeed = dicConf['PLSPE'] if 'PLSPE' in dicConf else 20.0
        self.pickupDelay = dicConf['PIDEL'] if 'PIDEL' in dicConf else 200.0
        self.placeDelay = dicConf['PLDEL'] if 'PLDEL' in dicConf else 200.0
        self.moveSpeed = dicConf['MVSPE'] if 'MVSPE' in dicConf else 20.0

    def aliasRemove(self, aliasStr):
        try:
            index = self.aliasList.index(aliasStr)
        except:
            print('alias inexistant')
        else:
            del self.aliasList[index]

    def aliasIsInModel(self, strAlias):
        """
        :param strAlias:
        :return 1 if alias is own list:
        """
        if strAlias in self.aliasList:
            return 1
        else:
            return 0


class ModDatabase:
    def __init__(self, path, logger):
        self.logger = logger
        self.pathFile = path
        self.dicMod = {}

        self.__loadFromFile()

    def findModelWithAlias(self, strAlias):
        """
        Find a modl with alias guiven in parameters.
        :param strAlias:
        :return the name of model find, return '' if nothing is found:
        """
        for mod in self.dicMod.values():
            if mod.aliasIsInModel(strAlias):
                return mod.name
        return 'Null'

    def __loadModel(self, cmlDesc):
        dicConf = {}
        aliasList = []
        dicConf['NAME'] = xe.getXmlValue(cmlDesc, 'name', 'null')
        dicConf['WIDTH'] = float(xe.getXmlValue(cmlDesc, 'width', 0.0))
        dicConf['LENGTH'] = float(xe.getXmlValue(cmlDesc, 'length', 0.0))
        dicConf['HEIGHT'] = float(xe.getXmlValue(cmlDesc, 'height', 0.0))
        dicConf['SCAN_HEIGHT'] = float(xe.getXmlValue(cmlDesc, 'scanHeight', 0.0))
        dicConf['PISPE'] = float(xe.getXmlValue(cmlDesc, 'pickupSpeed', 100.0))
        dicConf['PLSPE'] = float(xe.getXmlValue(cmlDesc, 'placeSpeed', 100.0))
        dicConf['PIDEL'] = float(xe.getXmlValue(cmlDesc, 'pickupDelay', 0.0))
        dicConf['PLDEL'] = float(xe.getXmlValue(cmlDesc, 'placeDelay', 0.0))
        dicConf['MVSPE'] = float(xe.getXmlValue(cmlDesc, 'moveSpeed', 100.0))

        aliasListXML = cmlDesc.find('alias')
        for alias in aliasListXML:
            aliasList.append(alias.text)
        dicConf['ALIAS'] = aliasList

        self.dicMod[dicConf['NAME']] = Model(dicConf)

    def __saveModel(self, model, rootMod):
        rootMod = etree.SubElement(rootMod, model.name)
        etree.SubElement(rootMod, "name").text = model.name
        etree.SubElement(rootMod, "width").text = str(model.width)
        etree.SubElement(rootMod, "length").text = str(model.length)
        etree.SubElement(rootMod, "height").text = str(model.height)
        etree.SubElement(rootMod, "scanHeight").text = str(model.scanHeight)
        etree.SubElement(rootMod, "pickupSpeed").text = str(model.pickupSpeed)
        etree.SubElement(rootMod, "placeSpeed").text = str(model.placeSpeed)
        etree.SubElement(rootMod, "pickupDelay").text = str(model.pickupDelay)
        etree.SubElement(rootMod, "placeDelay").text = str(model.placeDelay)
        etree.SubElement(rootMod, "moveSpeed").text = str(model.moveSpeed)

        rootList = etree.SubElement(rootMod, "alias")
        modelId = 0
        for alias in model.aliasList:
            etree.SubElement(rootList, 'A{}'.format(modelId)).text = alias
            modelId += 1

    def __loadFromFile(self):
        """
        Load data from xml file pointed by self.pathFile
        :return:
        """
        try:
            root = etree.parse(self.pathFile).getroot()
        except:
            self.logger.printCout("Error file don't exist: Make new model file")
            self.__makeNewFile()
        else:
            modList = root.find('model')
            # try:
            for mod in modList:
                self.__loadModel(mod)
            # except:
            #   self.logger.printCout("Error file error: Make new model file")
            #  self.__makeNewFile()

    def saveFile(self):

        root = etree.Element("root")
        modRoot = etree.SubElement(root, 'model')

        for mod in self.dicMod.values():
            self.__saveModel(mod, modRoot)

        with open(self.pathFile, 'wb') as fileOut:
            fileOut.write(etree.tostring(root, pretty_print=True))

    def __makeNewFile(self):
        """
        Make a new XML file wich is void.
        :return:
        """
        fileOut = open(self.pathFile, 'wb')
        root = etree.Element("root")
        etree.SubElement(root, 'model')
        fileOut.write(etree.tostring(root, pretty_print=True))
        fileOut.close()
        self.dicMod = {}

    def makeNewModel(self, name):
        dicConf = {'NAME': name, 'WIDTH': 0.0, 'LENGTH': 0.0, 'HEIGHT': 0.0, 'SCAN_HEIGHT': 0.0, 'ALIAS': list()}
        self.dicMod[name] = Model(dicConf)

    def __getitem__(self, index):
        return self.dicMod[index]

    def __setitem__(self, index, valeur):
        self.dicMod[index] = valeur

    def __len__(self):
        return len(self.dicMod)

    def __iter__(self):
        return self.dicMod.__iter__()

    def __next__(self):
        return self.dicMod.__next__()

    def deleteModule(self, modName):
        if modName in self.dicMod:
            del self.dicMod[modName]

    def values(self):
        return self.dicMod.values()


def boardSave(board, fileName):
    """
    Create and XML with board data.
    :param board:
    :param fileName:
    :return:
    """
    fileOut = open(fileName, 'wb')

    root = etree.Element("root")
    brd = etree.SubElement(root, "board")

    etree.SubElement(brd, "name").text = board.name
    etree.SubElement(brd, "ref1").text = board.ref1
    etree.SubElement(brd, "ref2").text = board.ref2
    etree.SubElement(brd, "Xsize").text = "{}".format(board.xSize)
    etree.SubElement(brd, "Ysize").text = "{}".format(board.ySize)
    etree.SubElement(brd, "Zsize").text = "{}".format(board.zSize)
    etree.SubElement(brd, "r1x").text = "{}".format(board.ref1RealPos['X'])
    etree.SubElement(brd, "r1y").text = "{}".format(board.ref1RealPos['Y'])
    etree.SubElement(brd, "r2x").text = "{}".format(board.ref2RealPos['X'])
    etree.SubElement(brd, "r2y").text = "{}".format(board.ref2RealPos['Y'])
    etree.SubElement(brd, "filtValue").text = board.filter['value']
    etree.SubElement(brd, "filtRef").text = board.filter['ref']
    etree.SubElement(brd, "filtPackage").text = board.filter['package']
    etree.SubElement(brd, "filtModel").text = board.filter['model']
    etree.SubElement(brd, "filtPlaced").text = board.filter['placed']
    etree.SubElement(brd, "filtEnable").text = board.filter['enable']


    cmpList = etree.SubElement(brd, "cmpList")

    cmpId = 0
    for cmp in board.cmpDic.values():
        cmpEntry = etree.SubElement(cmpList, "cmp")
        cmpEntry.set("data-id", "{}".format(cmpId))
        cmpId += 1

        etree.SubElement(cmpEntry, "ref").text = cmp.ref
        etree.SubElement(cmpEntry, "value").text = cmp.value
        etree.SubElement(cmpEntry, "package").text = cmp.package
        etree.SubElement(cmpEntry, "model").text = cmp.model
        etree.SubElement(cmpEntry, "feeder").text = "{}".format(cmp.feeder)
        etree.SubElement(cmpEntry, "posX").text = "{}".format(cmp.posX)
        etree.SubElement(cmpEntry, "posY").text = "{}".format(cmp.posY)
        etree.SubElement(cmpEntry, "angle").text = "{}".format(cmp.rot)
        etree.SubElement(cmpEntry, "placed").text = "{}".format(cmp.isPlaced)
        etree.SubElement(cmpEntry, "enable").text = "{}".format(cmp.isEnable)

    fileOut.write(etree.tostring(root, pretty_print=True))
    fileOut.close()


def boarLoad(path, logger):
    """
    Créate a board objects for xml file.
    :param logger:
    :param path: the path of the project file (pnpp):
    :return a board objet freshly créated: 
    """
    # fileIn = open(path, 'rb')

    root = etree.parse(path).getroot()
    brd = root.find('board')

    board = brr.Board(brd.find('name').text, logger)
    board.path = path

    board.xSize = float(xe.getXmlValue(brd, 'Xsize', 0.0))
    board.ySize = float(xe.getXmlValue(brd, 'Ysize', 0.0))
    board.zSize = float(xe.getXmlValue(brd, 'Zsize', 0.0))
    board.ref1 = xe.getXmlValue(brd, 'ref1', 'null')
    board.ref2 = xe.getXmlValue(brd, 'ref2', 'null')
    board.ref1RealPos['X'] = float(xe.getXmlValue(brd, 'r1x', 0.0))
    board.ref1RealPos['Y'] = float(xe.getXmlValue(brd, 'r1y', 0.0))
    board.ref2RealPos['X'] = float(xe.getXmlValue(brd, 'r2x', 0.0))
    board.ref2RealPos['Y'] = float(xe.getXmlValue(brd, 'r2y', 0.0))

    board.filter['value'] = xe.getXmlValue(brd, 'filtValue', '')
    board.filter['value'] = '' if board.filter['value'] is None else board.filter['value']
    board.filter['ref'] = xe.getXmlValue(brd, 'filtRef', '')
    board.filter['ref'] = '' if board.filter['ref'] is None else board.filter['ref']
    board.filter['package'] = xe.getXmlValue(brd, 'filtPackage', '')
    board.filter['package'] = '' if board.filter['package'] is None else board.filter['package']
    board.filter['model'] = xe.getXmlValue(brd, 'filtModel', '')
    board.filter['model'] = '' if board.filter['model'] is None else board.filter['model']
    board.filter['placed'] = xe.getXmlValue(brd, 'filtPlaced', '')
    board.filter['placed'] = '' if board.filter['placed'] is None else board.filter['placed']
    board.filter['enable'] = xe.getXmlValue(brd, 'filtEnable', '')
    board.filter['enable'] = '' if board.filter['enable'] is None else board.filter['enable']
    cmpList = brd.find('cmpList')

    for cmpXml in cmpList:
        cmpDesc = {'REF': xe.getXmlValue(cmpXml, 'ref', 'null'), 'VAL': xe.getXmlValue(cmpXml, 'value', 'null'),
                   'MOD': xe.getXmlValue(cmpXml, 'package', 'null'), 'X': float(xe.getXmlValue(cmpXml, 'posX', 0.0)),
                   'Y': float(xe.getXmlValue(cmpXml, 'posY', 0.0)), 'T': float(xe.getXmlValue(cmpXml, 'angle', 0.0))}

        cmp = brr.component(cmpDesc)
        cmp.model = xe.getXmlValue(cmpXml, 'model', 'null')
        cmp.feeder = xe.getXmlValue(cmpXml, 'feeder', 'null')
        cmp.isPlaced = int(xe.getXmlValue(cmpXml, 'placed', 0))
        cmp.isEnable = int(xe.getXmlValue(cmpXml, 'enable', 0))

        board[cmp.ref] = cmp  # Add new component to board

    return board
