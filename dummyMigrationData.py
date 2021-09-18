#!/usr/bin/env python3

####################################################################################################
#
# Generate dummy migration data
#
# The closer the orgUnits to each other, the more likely there is migration
# but there is a maximum odds of migration even if the orgUnit areas are touching each other.
#
# There is a maximum lat/long distance at which migration will happen, computed from the closest
# distance between points in each pair of orgUnits polygon coordinates:
#
#    distance = sqrt( (latitude1 - latitude2) ^ 2 + (longitude1 - longitude2) ^ 2 )
#
# The odds of migration decrease with the square of the distance between orgUnits.
#
# Migration odds in each direction between orgUnits are computed independently,
# so there may be migration in one direction between orgUnits, or the other direction, or both.
#
# The amount of migration is a random number chosen between 0 and an amount that starts with
# maxMigrationAmount for adjacent orgUnits and decreases to 0 as the distance reaches the maximum.
# The random amount of migration also drops off with the square of the distance between orgUnits.
#
# The data is written to the console, and so may be piped (or copied and pasted) to a file.
#
# When running on the Chiefdom level for the DHIS2 Sierra Leone demo, it may take a few minutes.
# (If you run it outputting to the terminal, you can see that the progress is steady.)
#
# When importing the data into DHIS2, you must choose under Advanced options:
#    Data element ID scheme: Code
#    Organisation Unit ID scheme: Code
#    ID scheme: Code
#
# This script requires:
#
#    pip install requests
#
####################################################################################################

import requests
import random

#
# Script parameters
#
instance = 'https://play.dhis2.org/dev' # DHIS2 instance
username = 'admin'
password = 'district'

migrationOddsBetweenAjacentAreas = 0.85 # Odds of any migration between adjacent orgUnit areas
maxMigrationDistance = 2.0 # Max migration distance for any migration in lat/long degrees
maxMigrationAmount = 10000 # Random from 0 to this number if orgUnits are adjacent, decreasing with distance to max distance

orgUnitLevel = 2 # Organisation unit level to map to category options
period = '202108' # DHIS2 Period into which to write the data
dataElement = 'MIGRATED_FROM_DISTRICT'

#
# Handy functions for accessing dhis 2
#
api = instance + '/api/'
credentials = ( username, password )

def d2get(args):
	return requests.get(api + args, auth=credentials).json()

#
# Fetch the organisation units to map to
#
orgUnits = d2get('organisationUnits?fields=code,geometry&filter=level:eq:' + str(orgUnitLevel) + '&paging=false')['organisationUnits']

#
# Find all the points within coordinates (nested with indeterminate and possibly ragged depth)
#
def points(coordinates):
	if isinstance(coordinates[0], float):
		return [coordinates]
	else:
		list = []
		for c in coordinates:
			list.extend(points(c))
		return list

#
# Find all the points within an orgUnit's coordinates
#
def ouPoints(orgUnit):
	return points(orgUnit['geometry']['coordinates'])

#
# Find the minimum distance (in degrees lat/long) between the points of two orgUnits' polygons
#
def minDistanceSquared(points1, points2):
	minSquared = 9999999
	for p1 in points1:
		for p2 in points2:
			minSquared = min( minSquared, (p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 )
	return minSquared

#
# Print a single data value
#
continuing = False

def printValue(toOu, fromOu, value):
	global continuing
	if continuing:
		print('        ,')
	continuing = True
	print('        {')
	print('            "dataElement": "' + dataElement + '",' )
	print('            "period": "' + period + '",' )
	print('            "orgUnit": "' + toOu['code'] + '",' )
	print('            "categoryOptionCombo": "' + fromOu['code'] + '",' )
	print('            "value": "' + str(value) + '"' )
	print('        }')

#
# Print out the data import
#

print('{')
print('    "dataValues": [')

for i in range(len(orgUnits)-1):
	points1 = ouPoints(orgUnits[i])
	for j in range(i+1,len(orgUnits)): # Only look at later orgUnits; earlier ones already done, and same orgUnit not applicable
		points2 = ouPoints(orgUnits[j])
		dSquared = minDistanceSquared(points1, points2)
		proximity = max((maxMigrationDistance**2 - dSquared) / maxMigrationDistance**2, 0.0) # 1 means touching, 0 means max migration distance (or more)
		migrationOdds = proximity * migrationOddsBetweenAjacentAreas # Odds on a scale of 0 to migrationOddsBetweenAjacentAreas
		migrationChoice = random.choices([1,0], [migrationOdds,1-migrationOdds], k=2) # roll the dice for migration to/from: 1 if migration 0 if not
		if migrationChoice[0]:
			migrationAmount = random.randrange(int(proximity * maxMigrationAmount))
			printValue(orgUnits[i], orgUnits[j], migrationAmount)
		if migrationChoice[1]:
			migrationAmount = random.randrange(int(proximity * maxMigrationAmount))
			printValue(orgUnits[j], orgUnits[i], migrationAmount)

print('    ]')
print('}')
