#!/usr/bin/env python3

####################################################################################################
#
# From a DHIS2 system, create a category and associated category combination, with
# category options linked to organisation units from a given level in the orgUnit hierarchy.
#
# This script requires:
#
#    pip install requests
#
####################################################################################################

import requests
import json

#
# Script parameters
#
instance = 'https://play.dhis2.org/dev' # DHIS2 instance
username = 'admin'
password = 'district'

orgUnitLevel = 3 # Organisation unit level to map to category options
categoryName = 'Chiefdoms' # Name of the category and category combination
categoryCode = 'CHIEFDOMS' # Code of the category and category combination

#
# Handy functions for accessing dhis 2
#
api = instance + '/api/'
credentials = ( username, password )

def d2get(args):
	print('\nGET', api + args) # debug
	response = requests.get(api + args, auth=credentials).json()
	print('response:', response, '\n')
	return response

def d2post(args, data):
	status = requests.post(api + args, json=data, auth=credentials)
	print('POST', status, api + args, json.dumps(data))

def d2put(args, data):
	status = requests.put(api + args, json=data, auth=credentials)
	print('PUT', status, api + args, json.dumps(data))

#
# Fetch the organisation units to map to
#
orgUnits = d2get('organisationUnits?fields=name,code,id&filter=level:eq:' + str(orgUnitLevel) + '&paging=false')['organisationUnits']

orgUnitCodes = ','.join([ou['code'] for ou in orgUnits])

#
# Create the category options
#
for ou in orgUnits:
	d2post('categoryOptions', {
		'name': ou['name'],
		'shortName': ou['name'][:50],
		'code': ou['code'],
		'organisationUnits': [
			{'id': ou['id'] }
			]
	} )

#
# Find the UIDs of the category options we just created
#
categoryOptions = d2get('categoryOptions?fields=id&filter=code:in:[' + orgUnitCodes + ']&paging=false')['categoryOptions']

#
# Create the category with all the options
#
d2post('categories', {
	'name': categoryName,
	'shortName': categoryName[:50],
	'code': categoryCode,
	'dataDimensionType': 'DISAGGREGATION',
	'dataDimension': True,
	'categoryOptions': categoryOptions
} )

#
# Find the UID of the category we just created
#
categories = d2get('categories?fields=id&filter=code:eq:' + categoryCode + '&paging=false')['categories']

#
# Create the category combination with the one category
#
d2post('categoryCombos', {
	'name': categoryName,
	'shortName': categoryName[:50],
	'code': categoryCode,
	'dataDimensionType': 'DISAGGREGATION',
	'categories': categories
} )

#
# Find the UID of the category combination we just created
#
categoryCombos = d2get('categoryCombos?fields=id&filter=code:eq:' + categoryCode + '&paging=false')['categoryCombos']

#
# Build category option combinations for the category combination
#
d2post('maintenance/categoryOptionComboUpdate/categoryCombo/' + categoryCombos[0]['id'], {})

#
# Get the category option with their attached category option combinations
#
categoryOptions = d2get('categoryOptions?fields=code,categoryOptionCombos[id,name,categoryCombo,categoryOptions],&filter=code:in:[' + orgUnitCodes + ']&paging=false')['categoryOptions']

#
# Copy codes from the category options to the category option combinations
#
for co in categoryOptions:
	coc = co['categoryOptionCombos'][0]
	coc['code'] = co['code']
	d2put('categoryOptionCombos/' + coc['id'] + '?mergeMode=REPLACE', coc )
