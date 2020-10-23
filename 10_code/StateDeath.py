import pandas as pd
from zipfile import ZipFile
import re

original_zip = ZipFile('US_VitalStatistics.zip', 'r')
new_zip = ZipFile('new_archve.zip', 'w')
for item in original_zip.infolist():
    buffer = original_zip.read(item.filename)
    if not str(item.filename).startswith('__MACOSX/'):
        new_zip.writestr(item, buffer)
new_zip.close()
original_zip.close()

new_zip = ZipFile('new_archve.zip', 'r')

dfs = {}

for text_file in new_zip.infolist():
    dfs[re.search('2\d\d\d', text_file.filename).group(0)] = pd.read_csv(new_zip.open(text_file.filename), sep = "\t", usecols = [1, 2, 3, 5, 7])[:-15]

dfs.keys()
origin = pd.DataFrame({})
for key in dfs.keys():
    origin = origin.append(dfs[key])
    pass

origin[origin['Deaths'] == 'Missing']['County'].unique()
index_names = origin[origin['Deaths'] == 'Missing'].index
origin = origin.drop(index_names)

origin['Deaths'] = origin['Deaths'].astype('int64')
origin['Year'] = origin['Year'].astype('int64')
origin['County Code'] = origin['County Code'].astype('int64')

totalDeath = origin.groupby(['County','Year','County Code'], as_index = False).sum()[['County','County Code','Year','Deaths']].rename({'Deaths':'TotalDeath'}, axis = 'columns')
totalDeath

names = []
for name in origin['Drug/Alcohol Induced Cause'].unique():
    if re.match('Drug poisonings.*', name):
        names.append(name)
        pass
    pass

interDose = origin[origin['Drug/Alcohol Induced Cause'].isin(names)]
finalDose = interDose.groupby(['County', 'County Code', 'Year'], as_index = False).sum()[['County','County Code','Year','Deaths']].rename({'Deaths':'TotalOverdose'}, axis = 'columns')
finalDose

final = pd.merge(finalDose, totalDeath, on = ['County', 'County Code', 'Year'])
final[['County','State']] = final.County.str.split(", ",expand=True,)
state = final.groupby(['State', 'Year'], as_index = False).sum().drop('County Code', axis = 1)
state['OverdoseProp'] = state['TotalOverdose'] / state['TotalDeath']

state['PolicyState'] = (state['State'] == 'FL') | ((state['State'] == 'TX')) | (state['State'] == 'WA')

nearFL = ['FL', 'LA', 'MS', 'SC']
nearTX = ['TX', 'AR', 'NM', 'KS']
nearWA = ['WA', 'CO', 'OR', 'CA']

state['Post'] = ((state['State'].isin(nearFL)) & (state['Year'] >= 2010)) | ((state['State'].isin(nearTX)) & (state['Year'] >= 2007)) | ((state['State'].isin(nearWA)) & (state['Year'] >= 2012))
state.to_csv('state_death.csv', index = False)
