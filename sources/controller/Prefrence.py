import configparser


class Preferences:
    def __init__(self, logger, path):
        self._config = configparser.ConfigParser()
        self._logger = logger
        self._path = path
        if not self._readConf():
            self._logger.printCout('Configuration file not found! Using default values.')
        self._formatForApp()

    def _formatForApp(self):
        """
        Put default value if needed.
        """
        if not 'PATH' in self._config:
            self._config['PATH'] = {}

        if not 'JOB' in self._config:
            self._config['JOB'] = {}

        if not 'machine' in self._config['PATH']:
            self._config['PATH']['machine'] = 'userdata/conf/machine.xml'

        if not 'mod' in self._config['PATH']:
            self._config['PATH']['mod'] = 'userdata/conf/mod.xml'

        if not 'homeCmpCount' in self._config['JOB']:
            self._config['JOB']['homeCmpCount'] = '100'

        if not 'errorManagement' in self._config['JOB']:
            self._config['JOB']['errorManagement'] = '0'

    def _readConf(self):
        try:
            self._config.read(self._path)
            return 1
        except:
            return 0

    def saveConf(self):
        with open(self._path, 'w') as configfile:
            self._config.write(configfile)

    def __getitem__(self, index):
        """Cette méthode spéciale est appelée quand on fait objet[index]
        Elle redirige vers self._dictionnaire[index]"""

        return self._config[index]

    def __setitem__(self, index, valeur):
        """Cette méthode est appelée quand on écrit objet[index] = valeur
        On redirige vers self._dictionnaire[index] = valeur"""

        self._config[index] = valeur

    def __len__(self):
        return len(self._config)

    def __iter__(self):
        return self._config.__iter__()

    def __next__(self):
        return self._config.__next__()


