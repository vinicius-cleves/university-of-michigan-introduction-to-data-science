import pandas as pd # '0.24.2'
import numpy as np  # '1.16.4'
from scipy.stats import ttest_ind # scipy.__version__ == '1.3.0'
from collections import namedtuple

#%% Use this dictionary to map state names to two letter acronyms
states = {'OH': 'Ohio', 'KY': 'Kentucky', 'AS': 'American Samoa', 'NV': 'Nevada', 'WY': 'Wyoming', 'NA': 'National', 'AL': 'Alabama', 'MD': 'Maryland', 'AK': 'Alaska', 'UT': 'Utah', 'OR': 'Oregon', 'MT': 'Montana', 'IL': 'Illinois', 'TN': 'Tennessee', 'DC': 'District of Columbia', 'VT': 'Vermont', 'ID': 'Idaho', 'AR': 'Arkansas', 'ME': 'Maine', 'WA': 'Washington', 'HI': 'Hawaii', 'WI': 'Wisconsin', 'MI': 'Michigan', 'IN': 'Indiana', 'NJ': 'New Jersey', 'AZ': 'Arizona', 'GU': 'Guam', 'MS': 'Mississippi', 'PR': 'Puerto Rico', 'NC': 'North Carolina', 'TX': 'Texas', 'SD': 'South Dakota', 'MP': 'Northern Mariana Islands', 'IA': 'Iowa', 'MO': 'Missouri', 'CT': 'Connecticut', 'WV': 'West Virginia', 'SC': 'South Carolina', 'LA': 'Louisiana', 'KS': 'Kansas', 'NY': 'New York', 'NE': 'Nebraska', 'OK': 'Oklahoma', 'FL': 'Florida', 'CA': 'California', 'CO': 'Colorado', 'PA': 'Pennsylvania', 'DE': 'Delaware', 'NM': 'New Mexico', 'RI': 'Rhode Island', 'MN': 'Minnesota', 'VI': 'Virgin Islands', 'NH': 'New Hampshire', 'MA': 'Massachusetts', 'GA': 'Georgia', 'ND': 'North Dakota', 'VA': 'Virginia'}

#%%
def get_list_of_university_towns():
    '''Returns a DataFrame of towns and the states they are in from the 
    university_towns.txt list. The format of the DataFrame should be:
    DataFrame( [ ["Michigan", "Ann Arbor"], ["Michigan", "Yipsilanti"] ], 
    columns=["State", "RegionName"]  )'''
    cities = []
    with open('university_towns.txt') as f:
        state = ''
        for line in f:
            line = line.strip()
            if '[edit]' in line:
                #its a state
                state = line[:-6] 
            elif line != '':
                #its a city
                city = line[ : line.find(' (')]
                cities.append([state, city])
            #else ignore empty line
    df = pd.DataFrame(cities, columns=['State','RegionName'])
    return df
#print(get_list_of_university_towns().head())

#%%
def get_recession_periods():
    s = pd.read_excel('gdplev.xls', skiprows=[0,1,2,3,4,6,7], usecols=[4,6], index_col=0, squeeze=True)
    #only interested in period after 2000 (inclusive)
    s = s[s.index >= '2000q1']
    #make sure it is sorted
    s = s.sort_index()
    #'q' must be upper case due to compatibility with other dataframes
    s.index = s.index.str.upper()
    #get possible starts and end of recessions
    #for long arrays of data, this could better be done with a state machine.
    #for now, the following is simpler
    snp = np.array(s)
    start = (snp[2:] < snp[1:-1]) & (snp[1:-1] < snp[:-2])
    end = ( (snp[4:] > snp[3:-1]) & 
            (snp[3:-1] > snp[2:-2]) & 
            (snp[2:-2] > snp[1:-3]) & 
            (snp[1:-3] > snp[:-4]) )
    start = np.insert(start, 0, [0]*2)
    end = np.insert(end, 0, [0]*4)
    #The economy is supposed to be ok in 2000. We look for a recession, 
    #them in a recession we look for its end and again for a recession and 
    #so forth
    begin = -1
    results = []
    for i in range(len(start)):
        if (begin == -1) and start[i] == True:
            begin = i
        elif (begin != -1) and end[i] == True:
            results.append([begin, i])
            begin = -1
    #produce tuples with (recession_start, recession_bottom, recession_end) periods
    final = []
    for result in results:
        final.append( (
            s.index[result[0]], 
            s.index[result[0]+np.argmin(snp[result[0]:result[1]])] , 
            s.index[result[1]]) )
    return final
#print(get_recession_periods())

#%%
def convert_housing_data_to_quarters():
    '''Converts the housing data to quarters and returns it as mean 
    values in a dataframe. This dataframe should be a dataframe with
    columns for 2000q1 through 2016q3, and should have a multi-index
    in the shape of ["State","RegionName"].
    '''
    df = pd.read_csv('City_Zhvi_AllHomes.csv')
    #drop useless columns and set index
    df = (df.drop(['RegionID', 'Metro', 'CountyName', 'SizeRank'], axis=1)
        .set_index(['State', 'RegionName']))
    #remaining columns are time-related
    df.columns = pd.to_datetime(df.columns)
    #filter the columns after the year 2000
    df= df.iloc[:, df.columns>=pd.Timestamp(year=2000, month=1, day=1)]
    #arrange in quarters
    df = df.groupby(df.columns.to_period('Q'), axis=1).mean()
    #rename index
    df = df.rename(index=states)#, level='State')
    #columns labels back to string type
    df.columns = df.columns.values.astype(str)
    #return sorted dataframe for better presentation
    return df.sort_index()
#print(convert_housing_data_to_quarters())

#%%
def run_ttest():
    #load data
    housing = convert_housing_data_to_quarters()
    unitowns = get_list_of_university_towns()
    recession_periods = get_recession_periods()
    
    #select relevant columns from housing
    starts  = [i[0] for i in recession_periods]
    bottons = [i[1] for i in recession_periods]
    ends    = [i[2] for i in recession_periods]
    housing = housing[starts+ends+bottons]
    rename = {}
    for i in starts:
        rename[i] = ('Start', i)
    for i in ends:
        rename[i] = ('End', i)
    for i in bottons:
        rename[i] = ('Bottom', i)
    housing = housing.rename(columns=rename)
    housing.columns = pd.MultiIndex.from_tuples(housing.columns, names=['l1','l2'])
    
    #visualize housing prices in start, bottom and end of a recession
    #print(housing)
    
    #group columns by caracteristics (start, end or bottom or recession)
    housing = housing.groupby(level=0, axis=1).mean().dropna()
    
    #merge unitowns to add Uni columns to data
    unitowns['Uni'] = 1
    housing = (housing.reset_index()
        .merge(unitowns, 
               how='left', 
               on=['State', 'RegionName'])
        .set_index(housing.index.names))
        
    housing_uni = housing[housing['Uni'] == 1]
    housing_not_uni = housing[housing['Uni'] != 1]
    
    rate_uni = (housing_uni['Bottom']/housing_uni['Start'])-1
    rate_not_uni = (housing_not_uni['Bottom']/housing_not_uni['Start'])-1
    
    p = ttest_ind(rate_uni, rate_not_uni)
    
    Result = namedtuple('Housing_in_recession', 'diferrent p better')
    return Result(
            p.pvalue<0.01, 
            p.pvalue, 
            'univeristy_town' 
                if rate_uni.mean() > rate_not_uni.mean() 
                else 'non-university town'
            )
    
    
    
if __name__ == "__main__":
    print(run_ttest())