import urllib.request
import sodapy
import json
import dml
import prov.model
import datetime
import uuid
import bson.code
from bson.json_util import dumps

class calculate_energy_ratio(dml.Algorithm):
    contributor = 'ajr10_williami'
    reads = ['ajr10_williami.area_spaces_cambridge',\
              'ajr10_williami.area_spaces_boston',\
              'ajr10_williami.clean_energy_cambridge',\
             'ajr10_williami.clean_energy_boston']
    writes = ['ajr10_williami.energy_ratio']

    @staticmethod
    def execute(trial = False):
        '''Retrieve some data sets and store in mongodb collections.'''
        startTime = datetime.datetime.now()

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('ajr10_williami', 'ajr10_williami')

        # Perform cleaning transformation here
        
        repo.dropCollection('ajr10_williami.energy_ratio')
        repo.createCollection('ajr10_williami.energy_ratio')

        open_spaces_cambridge = repo["ajr10_williami.area_spaces_cambridge"].find()
        open_spaces_boston = repo["ajr10_williami.area_spaces_boston"].find()
        energy_cambridge = repo["ajr10_williami.cleaned_energy_cambridge"].find()
        energy_boston = repo["ajr10_williami.cleaned_energy_boston"].find()

        energy_ratio_cambridge = {}
        energy_ratio_boston = {}
        energy_ratio_cambridge["total_open_space_cambridge"] = 0
        energy_ratio_boston["total_open_space_boston"] = 0
        energy_ratio_cambridge["total_CO2_cambridge"] = 0
        energy_ratio_boston["total_CO2_boston"] = 0
        energy_ratio_cambridge["total_mmbtu_cambridge"] = 0
        energy_ratio_boston["total_mmbtu_boston"] = 0

        # Known Data
        total_area_cambridge = 1.988 * pow(10,8) # 7.131 square miles
        total_area_boston = 2.4225 * pow(10,9) # 89.63 square miles
        population_cambridge = 107289 # as of 2013 census
        population_boston = 645966 # as of 2013 census

        for cambridge_open_space in open_spaces_cambridge:
            energy_ratio_cambridge["total_open_space_cambridge"] += eval(cambridge_open_space['area'])

        for cambridge_energy in energy_cambridge:
            energy_ratio_cambridge["total_CO2_cambridge"] += eval(cambridge_energy['CO2'])
            energy_ratio_cambridge["total_mmbtu_cambridge"] += eval(cambridge_energy['mmbtu'])

        for boston_open_space in open_spaces_boston:
            energy_ratio_boston["total_open_space_boston"] += boston_open_space['area']

        for boston_energy in energy_boston:
            energy_ratio_boston["total_CO2_boston"] += eval(boston_energy['CO2'])
            energy_ratio_boston["total_mmbtu_boston"] += eval(boston_energy['mmbtu'])

        # Calculate ratios and weights
        energy_ratio_cambridge["open_space_ratio_cambridge"] = energy_ratio_cambridge["total_open_space_cambridge"] / total_area_cambridge
        energy_ratio_boston["open_space_ratio_boston"] = energy_ratio_boston["total_open_space_boston"] / total_area_boston
        energy_ratio_cambridge["CO2_per_resident_cambridge"] = energy_ratio_cambridge["total_CO2_cambridge"] / population_cambridge
        energy_ratio_boston["CO2_per_resident_boston"] = energy_ratio_boston["total_CO2_boston"] / population_boston
        energy_ratio_cambridge["mmbtu_per_resident_cambridge"] = energy_ratio_cambridge["total_mmbtu_cambridge"] / population_cambridge
        energy_ratio_boston["mmbtu_per_resident_boston"] = energy_ratio_boston["total_mmbtu_boston"] / population_boston

        repo['ajr10_williami.energy_ratio'].insert(energy_ratio_cambridge)
        repo['ajr10_williami.energy_ratio'].insert(energy_ratio_boston)

        # logout and return start and end times
        repo.logout()
        endTime = datetime.datetime.now()
        return {"start":startTime, "end":endTime}
    
    @staticmethod
    def provenance(doc = prov.model.ProvDocument(), startTime = None, endTime = None):
        '''
        Create the provenance document describing everything happening
        in this script. Each run of the script will generate a new
        document describing that invocation event.
        '''

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('ajr10_williami', 'ajr10_williami')
        doc.add_namespace('alg', 'http://datamechanics.io/algorithm/') # The scripts are in <folder>#<filename> format.
        doc.add_namespace('dat', 'http://datamechanics.io/data/') # The data sets are in <user>#<collection> format.
        doc.add_namespace('ont', 'http://datamechanics.io/ontology#') # 'Extension', 'DataResource', 'DataSet', 'Retrieval', 'Query', or 'Computation'.
        doc.add_namespace('log', 'http://datamechanics.io/log/') # The event log.
        doc.add_namespace('cdp', 'https://data.cambridgema.gov/resource/')
        doc.add_namespace('bod', 'http://bostonopendata-boston.opendata.arcgis.com/datasets/')
        doc.add_namespace('cob', 'data.cityofboston.gov/')

        '''
        TODO: The entirety of this provenance code needs updating after execute() is finished being written

        this_script = doc.agent('alg:ajr10_williami#fetch_data', {prov.model.PROV_TYPE:prov.model.PROV['SoftwareAgent'], 'ont:Extension':'py'})
        open_spaces_cambridge_resource = doc.entity('cdp:5ctr-ccas', {'prov:label':'311, Service Requests', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})
        trees_cambridge_resource = doc.entity('cdp:q83f-7quz', {'prov:label':'311, Service Requests', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})
        open_spaces_boston_resource = doc.entity('bod:2868d370c55d4d458d4ae2224ef8cddd_7.geojson', {'prov:label':'311, Service Requests', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})
        trees_boston_resource = doc.entity('bod:ce863d38db284efe83555caf8a832e2a_1.geojson', {'prov:label':'311, Service Requests', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})
        energy_boston_resource = doc.entity('bod:exmd-natm', {'prov:label':'311, Service Requests', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})
        energy_cambridge_resource = doc.entity('cdp:es2i-g3p6', {'prov:label':'311, Service Requests', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})


        get_open_spaces_cambridge = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        get_trees_cambridge = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        get_open_spaces_boston = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        get_trees_boston = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        get_energy_boston = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        get_energy_cambridge = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        
        doc.wasAssociatedWith(get_open_spaces_cambridge, this_script)
        doc.wasAssociatedWith(get_trees_cambridge, this_script)
        doc.wasAssociatedWith(get_open_spaces_boston, this_script)
        doc.wasAssociatedWith(get_trees_boston, this_script)
        doc.wasAssociatedWith(get_energy_boston, this_script)
        doc.wasAssociatedWith(get_energy_cambridge, this_script)

        doc.usage(get_open_spaces_cambridge, open_spaces_cambridge_resource, startTime, None,
                  {prov.model.PROV_TYPE:'ont:Retrieval',
                  'ont:Query':'?type=Open+Spaces+Cambridge'
                  }
                  )
        doc.usage(get_trees_cambridge, trees_cambridge_resource, startTime, None,
                  {prov.model.PROV_TYPE:'ont:Retrieval',
                  'ont:Query':'?type=Trees+Cambridge'
                  }
                  )
        doc.usage(get_open_spaces_boston, open_spaces_boston_resource, startTime, None,
                  {prov.model.PROV_TYPE:'ont:Retrieval',
                  'ont:Query':'?type=Open+Spaces+Boston'
                  }
                  )
        doc.usage(get_trees_boston, trees_boston_resource, startTime, None,
                  {prov.model.PROV_TYPE:'ont:Retrieval',
                  'ont:Query':'?type=Trees+Boston'
                  }
                  )
        doc.usage(get_energy_boston, energy_boston_resource, startTime, None,
                  {prov.model.PROV_TYPE:'ont:Retrieval',
                  'ont:Query':'?type=Energy+Boston'
                  }
                  )
        doc.usage(get_energy_cambridge, energy_cambridge_resource, startTime, None,
                  {prov.model.PROV_TYPE:'ont:Retrieval',
                  'ont:Query':'?type=Energy+Cambridge'
                  }
                  )

        open_spaces_cambridge = doc.entity('dat:ajr10_williami#open_spaces_cambridge', {prov.model.PROV_LABEL:'Open spaces Cambridge', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(open_spaces_cambridge, this_script)
        doc.wasGeneratedBy(open_spaces_cambridge, get_open_spaces_cambridge, endTime)
        doc.wasDerivedFrom(open_spaces_cambridge, open_spaces_cambridge_resource, get_open_spaces_cambridge, get_open_spaces_cambridge, get_open_spaces_cambridge)

        trees_cambridge = doc.entity('dat:ajr10_williami#trees_cambridge', {prov.model.PROV_LABEL:'Trees Cambridge', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(trees_cambridge, this_script)
        doc.wasGeneratedBy(trees_cambridge, get_trees_cambridge, endTime)
        doc.wasDerivedFrom(trees_cambridge, trees_cambridge_resource, get_trees_cambridge, get_trees_cambridge, get_trees_cambridge)

        open_spaces_boston = doc.entity('dat:ajr10_williami#open_spaces_boston', {prov.model.PROV_LABEL:'Open spaces Boston', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(open_spaces_boston, this_script)
        doc.wasGeneratedBy(open_spaces_boston, get_open_spaces_boston, endTime)
        doc.wasDerivedFrom(open_spaces_boston, open_spaces_boston_resource, get_open_spaces_boston, get_open_spaces_boston, get_open_spaces_boston)

        trees_boston = doc.entity('dat:ajr10_williami#trees_boston', {prov.model.PROV_LABEL:'Trees Boston', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(trees_boston, this_script)
        doc.wasGeneratedBy(trees_boston, get_trees_boston, endTime)
        doc.wasDerivedFrom(trees_boston, trees_boston_resource, get_trees_boston, get_trees_boston, get_trees_boston)

        energy_boston = doc.entity('dat:ajr10_williami#energy_boston', {prov.model.PROV_LABEL:'Energy Boston', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(energy_boston, this_script)
        doc.wasGeneratedBy(energy_boston, get_energy_boston, endTime)
        doc.wasDerivedFrom(energy_boston, energy_boston_resource, get_energy_boston, get_energy_boston, get_energy_boston)

        energy_cambridge = doc.entity('dat:ajr10_williami#energy_cambridge', {prov.model.PROV_LABEL:'Energy Cambridge', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(energy_cambridge, this_script)
        doc.wasGeneratedBy(energy_cambridge, get_energy_cambridge, endTime)
        doc.wasDerivedFrom(energy_cambridge, energy_cambridge_resource, get_energy_cambridge, get_energy_cambridge, get_energy_cambridge)
        '''
        repo.logout()

        return doc

calculate_energy_ratio.execute()

# doc = calculate_energy_ratio.provenance()
# print(doc.get_provn())
# print(json.dumps(json.loads(doc.serialize()), indent=4))

## eof
