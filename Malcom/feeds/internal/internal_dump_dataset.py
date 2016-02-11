import codecs
from Malcom.feeds.core import Feed


class ExportAll(Feed):
    """
    This exports data from the db every 1h
    """
    def __init__(self):
        super(ExportAll, self).__init__(run_every="1h")
        self.description = "Export all the dataset to CSV and JSON"
        self.source = "local"
        self.tags = ['private', 'internal']

    def update(self):

        self.output_csv = codecs.open('{}/export_all.csv'.format(self.engine.configuration['EXPORTS_DIR']), 'w', "utf-8")
        self.output_csv.write(u"{},{},{},{},{},{}\n".format('Value', 'Type', 'Tags', 'First seen', 'Last seen', "Analyzed"))

        self.output_json = codecs.open('{}/export_all.json'.format(self.engine.configuration['EXPORTS_DIR']), 'w', "utf-8")
        self.output_json.write(u'[')
        for elt in self.model.elements.find({ "tags": {"$nin": ["whitelist"]}}):
            csv = elt.to_csv()
            self.output_csv.write(u"{}\n".format(csv))
            self.output_json.write(u"{}, ".format(elt.to_json()))

        self.output_csv.close()
        self.output_json.seek(-2, 2)  # nasty nasty hack
        self.output_json.write(u']')
        self.output_json.close()

    def analyze(self, dict, mode):
        pass
