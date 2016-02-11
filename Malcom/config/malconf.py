import ConfigParser
import os
import netifaces as ni


class MalcomSetup(dict):
    """Configuraiton loader"""
    def __init__(self):
        super(MalcomSetup, self).__init__()

    def save_config():
        raise NotImplemented

    def load_config(self, args):
        self.parse_command_line(args)
        self.sanitize_paths()
        self.get_network_interfaces()

    def sanitize_paths(self):
        if not self['SNIFFER_DIR'].startswith('/'):
            self['SNIFFER_DIR'] = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', self['SNIFFER_DIR']))
        if not self['MODULES_DIR'].startswith('/'):
            self['MODULES_DIR'] = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', self['MODULES_DIR']))
        if not self['YARA_PATH'].startswith('/'):
            self['YARA_PATH'] = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', self['YARA_PATH']))
        if not self['FEEDS_DIR'].startswith('/'):
            self['FEEDS_DIR'] = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', self['FEEDS_DIR']))
        if not self['EXPORTS_DIR'].startswith('/'):
            self['EXPORTS_DIR'] = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', self['EXPORTS_DIR']))

    def parse_command_line(self, args):

        if args.config:
            self.parse_config_file(args.config)
        else:
            self['LISTEN_INTERFACE'] = args.interface
            self['LISTEN_PORT'] = args.port
            self['MAX_WORKERS'] = args.max_workers
            self['TLS_PROXY_PORT'] = args.tls_proxy_port
            self['FEEDS'] = args.feeds
            self['SNIFFER'] = args.sniffer
            self['SNIFFER_NETWORK'] = False
            self['SNIFFER_DIR'] = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'sniffer', 'captures'))
            self['MODULES_DIR'] = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'sniffer', 'modules'))
            self['YARA_PATH'] = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'yara'))
            self['FEEDS_DIR'] = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'feeds'))
            self['ANALYTICS'] = args.analytics
            self['WEB'] = True
            self['AUTH'] = False

    def parse_config_file(self, filename):

        config = ConfigParser.ConfigParser(allow_no_value=True)
        config.read(filename)

        if config.has_section('web'):
            self['WEB'] = config.getboolean('web', 'activated')
            self['LISTEN_INTERFACE'] = config.get('web', 'listen_interface')
            self['LISTEN_PORT'] = config.getint('web', 'listen_port')
            self['AUTH'] = config.getboolean('web', 'auth')

        if config.has_section('analytics'):
            analytics_params = {key.upper(): val for key, val in config.items('analytics')}
            print analytics_params
            self.update(analytics_params)
            self['ANALYTICS'] = True if analytics_params['ACTIVATED'] == 'true' else False
            self['MAX_WORKERS'] = int(analytics_params['MAX_WORKERS'])
            self['SKIP_TAGS'] = analytics_params['SKIP_TAGS'].split(',') if analytics_params['SKIP_TAGS'] else []
            print self

        if config.has_section('feeds'):
            self['FEEDS'] = config.getboolean('feeds', 'activated')
            self['FEEDS_DIR'] = config.get('feeds', 'feeds_dir')
            self['FEEDS_SCHEDULER'] = config.getboolean('feeds', 'scheduler')
            self['EXPORTS_DIR'] = config.get('feeds', 'exports_dir')

        if config.has_section('sniffer'):
            sniffer_params = {key.upper(): val for key, val in config.items('sniffer')}
            self.update(sniffer_params)
            self['SNIFFER'] = True if sniffer_params['ACTIVATED'] == 'true' else False
            self['TLS_PROXY_PORT'] = int(sniffer_params['TLS_PROXY_PORT'])
            self['SNIFFER_NETWORK'] = True if sniffer_params['NETWORK'] == 'true' else False


        if config.has_section('database'):
            self['DATABASE'] = {}
            db_params = dict(config.items('database'))
            if 'hosts' in db_params:
                self['DATABASE']['HOSTS'] = db_params['hosts'].split(',')
            if 'name' in db_params:
                self['DATABASE']['NAME'] = db_params['name']
            if 'username' in db_params:
                self['DATABASE']['USERNAME'] = db_params['username']
            if 'password' in db_params:
                self['DATABASE']['PASSWORD'] = db_params['password']
            if 'authentication_database' in db_params:
                self['DATABASE']['SOURCE'] = db_params['authentication_database']
            if 'replset' in db_params:
                self['DATABASE']['REPLSET'] = db_params['replset']
            if 'read_preferences' in db_params:
                self['DATABASE']['READ_PREF'] = db_params['read_preferences']

        if config.has_section('modules'):
            self['ACTIVATED_MODULES'] = []
            for module in config.options('modules'):
                self['ACTIVATED_MODULES'].append(module)

    def get_network_interfaces(self):
        self['IFACES'] = {}
        for i in [i for i in ni.interfaces() if i.find('eth') != -1]:
            self['IFACES'][i] = ni.ifaddresses(i).get(2, [{'addr': 'Not defined'}])[0]['addr']

    def to_dict(self):
        return self.__dict__

    def __getattr__(self, name):
        return self.get(name, None)

    def __setattr__(self, name, value):
        self[name] = value
