# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_core.ipynb.

# %% auto 0
__all__ = ['seasons', 'days', 'EWH_RANGE', 'parameters', 'read_directory_part1', 'read_directory_part2', 'save_directory_part1',
           'save_directory_part2', 'semi_differentiated_index', 'source_data', 'flow_data', 'cluster_data',
           'event_data', 'profile_data', 'get_source_data', 'get_flow_data', 'find_flow', 'get_cluster_data',
           'get_clusters', 'get_event_parameters', 'get_cluster_probability', 'get_centroid', 'get_gauss',
           'pick_from_gauss', 'elbow_method', 'elbow_method_2', 'list_to_coordinates', 'cluster', 'cluster_2',
           'get_event_data', 'get_events', 'pick_from_fitted_gauss', 'combine_volumes', 'pick_random_event',
           'pick_nominal_event', 'get_profile_data', 'get_profile', 'save_profiles']

# %% ../nbs/00_core.ipynb 3
import pandas as pd
import numpy as np
import math
from sklearn.cluster import KMeans
import random
from random import randrange
from scipy.stats import norm
import warnings
warnings.filterwarnings("ignore")

# %% ../nbs/00_core.ipynb 4
seasons = ['Summer', 'Autumn', 'Winter', 'Spring']
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

#==============
#Parameters
#==============

EWH_RANGE = [0,1]

parameters = {}
parameters = {
    "mode": 'nominal', # real = /conservative/nominal
    "considered_weeks": 12, # number of weeks to read in from Input Data
    "desired_weeks":4, # number of weeks to generate for Output Data
    "differentiated_days": 'yes', # 'yes' to include this data set/ 'no' to leave out
    "semi-differentiated_days": 'yes', # 'yes' to include this data set/ 'no' to leave out
    "undifferentiated_days": 'yes', # 'yes' to include this data set/ 'no' to leave out
    "max_time_clusters":7, # Time cluster limit
    "max_volume_clusters":3, # Voume cluster limit
    "elbow_tolerance_time":0.01, # Time clustering tolerance, smaller value = more clusters
    "elbow_tolerance_volume":0.2, # Volume clustering tolerance, smaller value = more clusters
    "impulse_usages":0, # 1 = all water events will have duration of 1 minute/ 0 = normal
}

# Read directory

read_directory_part1 = 'InputData/ewh_profile['
read_directory_part2 = '].csv'

# Save directory

save_directory_part1 = 'OutputData/' + parameters["mode"] + '/synthetic_profile['
save_directory_part2 = '].csv'

# Generate indices for weekdays and weekends:

semi_differentiated_index = {}
semi_differentiated_index['weekdays'] = [0,1,2,3,4]
semi_differentiated_index['weekends'] = [5,6]
for i in range(parameters["considered_weeks"]-1):
    for j in range(5):
        semi_differentiated_index['weekdays'].append(semi_differentiated_index['weekdays'][-5]+7)
    for j in range(2):
        semi_differentiated_index['weekends'].append(semi_differentiated_index['weekends'][-2]+7)

# %% ../nbs/00_core.ipynb 5
def get_source_data(ewh_id):
    read_data = pd.read_csv(read_directory_part1 + str(ewh_id) + read_directory_part2, sep=',',header=None, na_values = '-', skiprows = 1)
    source_data = {}
    for s in range(len(seasons)):
        source_data[seasons[s]] = list(read_data[4*s+1])
    return source_data

def get_flow_data(source_data):
    flow_data = {}
    if(parameters["differentiated_days"] == 'yes'):
        for d in range(len(days)):
            flow_data[days[d]] = {}
            for w in range(parameters["considered_weeks"]):
                flow_data[days[d]][w] = find_flow(source_data[(w*1440*7 + d*1440):(w*1440*7 + (d+1)*1440)])
    if(parameters["semi-differentiated_days"] == 'yes'):
        flow_data['weekdays'] = {}
        for d in range(len(semi_differentiated_index['weekdays'])):
            flow_data['weekdays'][d] = find_flow(source_data[(semi_differentiated_index['weekdays'][d]*1440):((semi_differentiated_index['weekdays'][d]+1)*1440)])
        flow_data['weekends'] = {}    
        for d in range(len(semi_differentiated_index['weekends'])):    
            flow_data['weekends'][d] = find_flow(source_data[(semi_differentiated_index['weekends'][d]*1440):((semi_differentiated_index['weekends'][d]+1)*1440)])
    if(parameters["undifferentiated_days"] == 'yes'):
        flow_data['all'] = {}
        for d in range(7*parameters["considered_weeks"]):
            flow_data['all'][d] = find_flow(source_data[(d*1440):((d+1)*1440)])
    return flow_data

def find_flow(source_data):
    flows = {}
    flows['time_bins'] = []
    flows['flow_rate'] = []
    for t in range(len(source_data)):
        if(source_data[t] > 0):
            flows['time_bins'].append(t)
            flows['flow_rate'].append(source_data[t])
    return flows

def get_cluster_data(flow_data):
    cluster_data = {}
    if(parameters["differentiated_days"] == 'yes'):
        for d in range(len(days)):
            cluster_data[days[d]] = {}
            temp_cluster_data = {}
            temp_cluster_data['time_bins'] = []
            temp_cluster_data['flow_rate'] = []
            for w in range(parameters["considered_weeks"]):
                temp_cluster_data['time_bins'].extend(flow_data[days[d]][w]['time_bins'])
                temp_cluster_data['flow_rate'].extend(flow_data[days[d]][w]['flow_rate'])
            cluster_data[days[d]] = get_clusters(cluster_data[days[d]], temp_cluster_data, "differentiated_days", flow_data[days[d]])
    if(parameters["semi-differentiated_days"] == 'yes'):
            cluster_data['weekdays'] = {}
            temp_cluster_data = {}
            temp_cluster_data['time_bins'] = []
            temp_cluster_data['flow_rate'] = []
            for w in range(len(semi_differentiated_index['weekdays'])):
                temp_cluster_data['time_bins'].extend(flow_data['weekdays'][w]['time_bins'])
                temp_cluster_data['flow_rate'].extend(flow_data['weekdays'][w]['flow_rate'])
            cluster_data['weekdays'] = get_clusters(cluster_data['weekdays'], temp_cluster_data, "semi-differentiated_days1", flow_data['weekdays'])
            cluster_data['weekends'] = {}
            temp_cluster_data = {}
            temp_cluster_data['time_bins'] = []
            temp_cluster_data['flow_rate'] = []
            for w in range(len(semi_differentiated_index['weekends'])):
                temp_cluster_data['time_bins'].extend(flow_data['weekends'][w]['time_bins'])
                temp_cluster_data['flow_rate'].extend(flow_data['weekends'][w]['flow_rate'])
            cluster_data['weekends'] = get_clusters(cluster_data['weekends'], temp_cluster_data, "semi-differentiated_days2", flow_data['weekends'])
    if(parameters["undifferentiated_days"] == 'yes'):
            cluster_data['all'] = {}
            temp_cluster_data = {}
            temp_cluster_data['time_bins'] = []
            temp_cluster_data['flow_rate'] = []
            for w in range(len(list(range(7*parameters["considered_weeks"])))):
                temp_cluster_data['time_bins'].extend(flow_data['all'][w]['time_bins'])
                temp_cluster_data['flow_rate'].extend(flow_data['all'][w]['flow_rate'])
            cluster_data['all'] = get_clusters(cluster_data['all'], temp_cluster_data, "undifferentiated_days", flow_data['all'])

    return cluster_data
    
def get_clusters(cluster_data, temp_cluster_data, day_type, flow_data):
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
    cluster_data['time_cluster_amount'] = elbow_method(temp_cluster_data, parameters["max_time_clusters"], 'time_bins', parameters["elbow_tolerance_time"])
    cluster_data['time_cluster'] = {}
    cluster_data['time_cluster']['event_starts'] = {}
    cluster_data['time_cluster']['event_volumes'] = {}
    cluster_data['time_cluster']['event_flow_rates'] = {}
    cluster_data['time_cluster']['time_boundaries'] = {}
    cluster_data['time_cluster']['null_probability'] = {}
    cluster_data['time_cluster']['start_model'] = {}
    
    if(cluster_data['time_cluster_amount'] > 0):
        cluster_data['time_cluster']['time_bins'], cluster_data['time_cluster']['flow_rate'] = cluster(cluster_data['time_cluster_amount'], temp_cluster_data, 'time_bins')
    
    for t in range(cluster_data['time_cluster_amount']):
        cluster_data['time_cluster']['time_boundaries'][t] = [min(cluster_data['time_cluster']['time_bins'][t]),max(cluster_data['time_cluster']['time_bins'][t])]
        cluster_data['time_cluster']['event_starts'][t], cluster_data['time_cluster']['event_volumes'][t], cluster_data['time_cluster']['event_flow_rates'][t] = get_event_parameters(flow_data, cluster_data['time_cluster']['time_boundaries'][t]) 
        cluster_data['time_cluster']['start_model'][t] = get_gauss(cluster_data['time_cluster']['time_bins'][t])
    cluster_data['flow_cluster'] = {}
    cluster_data['flow_cluster']['flow_boundaries'] = {}
    cluster_data['flow_cluster']['volume_boundaries'] = {}
    cluster_data['flow_cluster']['volume'] = {}
    cluster_data['flow_cluster']['flow_rate'] = {}
    cluster_data['flow_cluster']['probability'] = {}
    cluster_data['flow_cluster']['covariance'] = {}
    cluster_data['flow_cluster']['mean'] = {}
    
    for t in range(cluster_data['time_cluster_amount']):
        new_temp_cluster = {}
        new_temp_cluster['volume'] = cluster_data['time_cluster']['event_volumes'][t]
        new_temp_cluster['flow_rate'] = cluster_data['time_cluster']['event_flow_rates'][t]
        cluster_data['flow_cluster']['flow_boundaries'][t] = {}
        cluster_data['flow_cluster']['volume_boundaries'][t] = {}
        cluster_data['flow_cluster']['probability'][t] = {}
        cluster_data['flow_cluster']['covariance'][t] = {}
        cluster_data['flow_cluster']['mean'][t] = {}
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cluster_data['flow_cluster_amount'] = elbow_method_2(new_temp_cluster, parameters["max_volume_clusters"], 'volume', parameters["elbow_tolerance_volume"])
        if(cluster_data['flow_cluster_amount'] > 0):
            cluster_data['flow_cluster']['volume'][t], cluster_data['flow_cluster']['flow_rate'][t] = cluster_2(cluster_data['flow_cluster_amount'], new_temp_cluster, 'volume')
        temp_probability = 0
        for f in range(cluster_data['flow_cluster_amount']):
            cluster_data['flow_cluster']['flow_boundaries'][t][f] = [min(cluster_data['flow_cluster']['flow_rate'][t][f]),max(cluster_data['flow_cluster']['flow_rate'][t][f])]
            cluster_data['flow_cluster']['volume_boundaries'][t][f] = [min(cluster_data['flow_cluster']['volume'][t][f]),max(cluster_data['flow_cluster']['volume'][t][f])]
            if(len(cluster_data['flow_cluster']['flow_rate'][t][f]) < 2):
                cluster_data['flow_cluster']['covariance'][t][f] = [[0,0],[0,0]]
                cluster_data['flow_cluster']['mean'][t][f] = [cluster_data['flow_cluster']['flow_rate'][t][f][0],cluster_data['flow_cluster']['volume'][t][f][0]]
            else:
                cluster_data['flow_cluster']['covariance'][t][f] = np.cov(cluster_data['flow_cluster']['flow_rate'][t][f], cluster_data['flow_cluster']['volume'][t][f])*(0.1)
                cluster_data['flow_cluster']['mean'][t][f] = [np.mean(cluster_data['flow_cluster']['flow_rate'][t][f]), np.mean(cluster_data['flow_cluster']['volume'][t][f])]
            cluster_data['flow_cluster']['probability'][t][f] = get_cluster_probability(day_type, flow_data, cluster_data['flow_cluster']['flow_boundaries'][t][f], cluster_data['flow_cluster']['volume_boundaries'][t][f], cluster_data['time_cluster']['time_boundaries'][t])    
            temp_probability += cluster_data['flow_cluster']['probability'][t][f]
        cluster_data['time_cluster']['null_probability'][t] = 100 - temp_probability
    return cluster_data

def get_event_parameters(flow_rates, time_boundaries):
    event_starts = []
    event_volumes = []
    event_flow_rates = []
    for f in range(len(flow_rates)):
        temp_event_flows = []
        for x in range(len(flow_rates[f]['time_bins'])):
            if(time_boundaries[0] <= flow_rates[f]['time_bins'][x] <= time_boundaries[1]):
                event_starts.append(flow_rates[f]['time_bins'][x])
                temp_event_flows.append(flow_rates[f]['flow_rate'][x])
        if(len(temp_event_flows) > 0):
            event_volumes.append(sum(temp_event_flows))
            event_flow_rates.append(sum(temp_event_flows)/len(temp_event_flows))
    return event_starts, event_volumes, event_flow_rates

def get_cluster_probability(day_type, flow_rates, flow_boundaries, volume_boundaries, time_boundaries):
    numerator = 0
    if(day_type == "differentiated_days"):denominator = parameters["considered_weeks"]
    elif(day_type == "semi-differentiated_days1"):denominator = parameters["considered_weeks"]*5
    elif(day_type == "semi-differentiated_days2"):denominator = parameters["considered_weeks"]*2
    elif(day_type == "undifferentiated_days"):denominator = parameters["considered_weeks"]*7
        
    event_volumes = []
    event_flow_rates = []

    for f in range(len(flow_rates)):
        found = 0
        temp_flows = []
        for g in range(len(flow_rates[f]['time_bins'])):
            if(time_boundaries[0] <= flow_rates[f]['time_bins'][g] <= time_boundaries[1]):
                temp_flows.append(flow_rates[f]['flow_rate'][g])
        if(len(temp_flows) > 0):
            event_volumes.append(sum(temp_flows))
            event_flow_rates.append(sum(temp_flows)/len(temp_flows))
    for i in range(len(event_volumes)):
        if(flow_boundaries[0] <= event_flow_rates[i] <= flow_boundaries[1]):
            if(volume_boundaries[0] <= event_volumes[i] <= volume_boundaries[1]):
                numerator += 1
    return (numerator/denominator)*100

def get_centroid(time_boundaries, flow_rates):
    centroids = []
    for f in range(len(flow_rates)):
        cluster_flow_rates = []
        for x in range(len(flow_rates[f]['time_bins'])):
            if(time_boundaries[0] <= flow_rates[f]['time_bins'][x] <= time_boundaries[1]):
                cluster_flow_rates.append(flow_rates[f]['flow_rate'][x])
        if(len(cluster_flow_rates) > 0):
            if(len(cluster_flow_rates)%2 == 0): #if even
                median = np.percentile(cluster_flow_rates, 50)
                middle_left = cluster_flow_rates[int(len(cluster_flow_rates)/2-1)]
                middle_right = cluster_flow_rates[int(len(cluster_flow_rates)/2)]
                if(median - middle_left <= middle_right - median):
                    centroids.append(middle_left)
                else:
                    centroids.append(middle_right)
            else: #if odd
                centroids.append(np.percentile(cluster_flow_rates, 50))
    return centroids

def get_gauss(data):
    new_data = {}
    if(len(data) > 1):
        sample_mean = np.mean(data)
        sample_std = np.std(data)
        dist = norm(sample_mean, sample_std)
        new_data['values'] = [new_data['values'] for new_data['values'] in range(min(data)-100, max(data)+100)]
        temp_values = new_data['values'].copy()
        probabilities = [dist.pdf(temp_values) for temp_values in temp_values]
        new_data['cum_probability'] = []
        current = 0
        for i in range(len(probabilities)):
            current += probabilities[i]
            new_data['cum_probability'].append(current)
        new_data['cum_probability'].append(1)
    else:
        new_data['values'] = [data[0]]
        new_data['cum_probability'] = [0,1]
    return new_data
        
def pick_from_gauss(data, time_bins):
    valid = 0
    while(valid == 0):
        x = random.uniform(0, 1)
        picked_sample = min(time_bins)
        for j in range(len(data['cum_probability'])-1):
            if(data['cum_probability'][j] <= x < data['cum_probability'][j+1]):
                picked_sample = data['values'][j]
        if(min(time_bins) <= picked_sample <= max(time_bins)):valid = 1
    return picked_sample

def elbow_method(cluster_data, max_clusters, cluster_type, elbow_tolerance):
    unique_length = len([list(x) for x in set(tuple(x) for x in list_to_coordinates(cluster_data['time_bins'], cluster_data['flow_rate']))])
    if(unique_length >= 1):
        Y = np.array(cluster_data[cluster_type]).reshape(-1,1)
        if(unique_length < max_clusters):
            kmeans = [KMeans(n_clusters=i) for i in range(1, unique_length+1)]
        else:
            kmeans = [KMeans(n_clusters=i) for i in range(1, max_clusters+1)]
        score = [kmeans[i].fit(Y).score(Y) for i in range(len(kmeans))]
        new_score = []
        if(abs(score[0]) == 0):
            return 1
        else:
            for i in range(len(score)):
                new_score.append(abs(score[i])/abs(score[0]))
            delta = new_score[0]
            i = 0
            while(delta > elbow_tolerance and i < unique_length-1 and i < max_clusters-1):
                i += 1
                delta = abs(new_score[i-1]) - abs(new_score[i])
            if(i == 0):i = 1
            return i
    else:
        return 0
    
def elbow_method_2(cluster_data, max_clusters, cluster_type, elbow_tolerance):
    unique_length = len([list(x) for x in set(tuple(x) for x in list_to_coordinates(cluster_data['volume'], cluster_data['flow_rate']))])
    if(unique_length >= 1):
        Y = np.array(cluster_data[cluster_type]).reshape(-1,1)
        if(unique_length < max_clusters):
            kmeans = [KMeans(n_clusters=i) for i in range(1, unique_length+1)]
        else:
            kmeans = [KMeans(n_clusters=i) for i in range(1, max_clusters+1)]
        score = [kmeans[i].fit(Y).score(Y) for i in range(len(kmeans))]
        new_score = []
        if(abs(score[0]) == 0):
            return 1
        else:
            for i in range(len(score)):
                new_score.append(abs(score[i])/abs(score[0]))
            delta = new_score[0]
            i = 0
            while(delta > elbow_tolerance and i < unique_length-1 and i < max_clusters-1):
                i += 1
                delta = abs(new_score[i-1]) - abs(new_score[i])
            if(i == 0):i = 1
            return i
    else:
        return 0
    
def list_to_coordinates(list_1, list_2):
    return [list(z) for z in zip(list_1, list_2)]

def cluster(cluster_amount, cluster_data, cluster_type):
    old_data = {}
    old_data['time_bins'] = {}
    old_data['flow_rate'] = {}
    
    Y = np.array(cluster_data[cluster_type]).reshape(-1,1)    
    clustered_data = KMeans(cluster_amount, random_state = 0).fit(Y)
    for i in range(cluster_amount):
        old_data['time_bins'][i] = []
        old_data['flow_rate'][i] = []
    for j in range(len(clustered_data.labels_)):
        old_data['time_bins'][clustered_data.labels_[j]].append(cluster_data['time_bins'][j])
        old_data['flow_rate'][clustered_data.labels_[j]].append(cluster_data['flow_rate'][j])
    first_samples = []
    for i in range(cluster_amount):
        first_samples.append(min(old_data[cluster_type][i]))
    sort_list = sorted(range(len(first_samples)), key=lambda k: first_samples[k])
    data = {}
    data['time_bins'] = {}
    data['flow_rate'] = {}
    for i in range(len(sort_list)):
        data['time_bins'][i] = old_data['time_bins'][sort_list[i]]
        data['flow_rate'][i] = old_data['flow_rate'][sort_list[i]]
    return data['time_bins'], data['flow_rate']

def cluster_2(cluster_amount, cluster_data, cluster_type):
    old_data = {}
    old_data['volume'] = {}
    old_data['flow_rate'] = {}
    
    Y = np.array(cluster_data[cluster_type]).reshape(-1,1)    
    clustered_data = KMeans(cluster_amount, random_state = 0).fit(Y)
    for i in range(cluster_amount):
        old_data['volume'][i] = []
        old_data['flow_rate'][i] = []
    for j in range(len(clustered_data.labels_)):
        old_data['volume'][clustered_data.labels_[j]].append(cluster_data['volume'][j])
        old_data['flow_rate'][clustered_data.labels_[j]].append(cluster_data['flow_rate'][j])
    first_samples = []
    for i in range(cluster_amount):
        first_samples.append(min(old_data[cluster_type][i]))
    sort_list = sorted(range(len(first_samples)), key=lambda k: first_samples[k])
    data = {}
    data['volume'] = {}
    data['flow_rate'] = {}
    for i in range(len(sort_list)):
        data['volume'][i] = old_data['volume'][sort_list[i]]
        data['flow_rate'][i] = old_data['flow_rate'][sort_list[i]]
    return data['volume'], data['flow_rate']

def get_event_data(cluster_data):
    event_data = {}
    if(parameters["differentiated_days"] == 'yes'):
        for d in range(len(days)):
            event_data[days[d]] = get_events(cluster_data[days[d]], parameters["desired_weeks"])
    if(parameters["semi-differentiated_days"] == 'yes'):
        for d in range(5):
            event_data['weekday_' + str(d)] = get_events(cluster_data['weekdays'], parameters["desired_weeks"])
        for d in range(5,7):
            event_data['weekday_' + str(d)] = get_events(cluster_data['weekends'], parameters["desired_weeks"])
    if(parameters["undifferentiated_days"] == 'yes'):
        for d in range(len(days)):
            event_data['all_' + str(d)] = get_events(cluster_data['all'], parameters["desired_weeks"])
    return event_data

def get_events(cluster_data, day_amount):
    events = {}
    events['event_starts'] = {}
    events['event_volumes'] = {}
    events['event_flow_rates'] = {}
    for w in range(day_amount):
        events['event_starts'][w] = []
        events['event_volumes'][w] = []
        events['event_flow_rates'][w] = []
        for t in range(cluster_data['time_cluster_amount']):
            if(parameters["mode"] == 'nominal'):
                flow_event_occurence = pick_nominal_event(cluster_data, t)
                events['event_starts'][w].append(int(np.percentile(cluster_data['time_cluster']['time_bins'][t], 50)))
                events['event_volumes'][w].append(np.percentile(cluster_data['flow_cluster']['volume'][t][flow_event_occurence], 50))
                events['event_flow_rates'][w].append(np.percentile(cluster_data['flow_cluster']['flow_rate'][t][flow_event_occurence], 50))
            elif(parameters["mode"] == 'conservative'):
                events['event_starts'][w].append(int(np.percentile(cluster_data['time_cluster']['time_bins'][t], 0)))
                volumes = list(filter(lambda num: num != 0, cluster_data['flow_cluster']['volume'][t][len(cluster_data['flow_cluster']['volume'][t])-1]))
                events['event_volumes'][w].append(np.percentile(volumes, 100))
                events['event_flow_rates'][w].append(np.percentile(cluster_data['flow_cluster']['flow_rate'][t][len(cluster_data['flow_cluster']['volume'][t])-1], 50))
            elif(parameters["mode"] == 'real'):       
                flow_event_occurence = pick_random_event(cluster_data, t)
                if(flow_event_occurence != -1):
                    events['event_starts'][w].append(pick_from_gauss(cluster_data['time_cluster']['start_model'][t], cluster_data['time_cluster']['time_bins'][t]))
                    event_volume, event_flow_rate = pick_from_fitted_gauss(cluster_data['flow_cluster']['covariance'][t][flow_event_occurence], cluster_data['flow_cluster']['mean'][t][flow_event_occurence])
                    events['event_volumes'][w].append(event_volume)
                    events['event_flow_rates'][w].append(event_flow_rate)
    return events

def pick_from_fitted_gauss(covariance, mean):
    gauss = [[-1,-1]]
    while(gauss[0][0]<=0 or gauss[0][1]<=0):
        gauss = np.random.multivariate_normal(mean, covariance, 1)
    return gauss[0][1], gauss[0][0]
    
def combine_volumes(event_volumes, volume_index):
    volume = 0
    temp_volume = []
    for i in range(len(event_volumes)):
        temp_volume.append(event_volumes[i][volume_index])
        volume += event_volumes[i][volume_index]
    return volume

def pick_random_event(cluster_data, time_cluster):
    
    probability_list = [0]
    for f in range(len(cluster_data['flow_cluster']['probability'][time_cluster])):
        if(cluster_data['flow_cluster']['probability'][time_cluster][f] > 0):
            probability_list.append(probability_list[-1] + cluster_data['flow_cluster']['probability'][time_cluster][f]/100)
    x = random.uniform(0, 1)
    chosen_flow_cluster = -1 #-1 means that no flow cluster occurs for the time slot
    for f in range(len(probability_list)-1):
        if(probability_list[f] <= x < probability_list[f+1]):chosen_flow_cluster = f
    return chosen_flow_cluster 

def pick_nominal_event(cluster_data, time_cluster):
    
    probability_list = [0]
    for f in range(len(cluster_data['flow_cluster']['probability'][time_cluster])):
        if(cluster_data['flow_cluster']['probability'][time_cluster][f] > 0):
            probability_list.append(probability_list[-1] + cluster_data['flow_cluster']['probability'][time_cluster][f]/100)
    chosen_flow_cluster = -1 #-1 means that no flow cluster occurs for the time slot
    x = 0
    for f in range(len(probability_list)-1):
        if((probability_list[f+1] - probability_list[f]) > x):
            x = (probability_list[f+1] - probability_list[f])
            chosen_flow_cluster = f
    return chosen_flow_cluster 

def get_profile_data(event_data):
    profile_data = {}
    if(parameters["differentiated_days"] == 'yes'):
        profile_data["differentiated_days"] = []
        for w in range(parameters["desired_weeks"]):
            for d in range(len(days)):
                profile_data["differentiated_days"].extend(get_profile(event_data[days[d]]['event_starts'][w], event_data[days[d]]['event_volumes'][w], event_data[days[d]]['event_flow_rates'][w]))
    if(parameters["semi-differentiated_days"] == 'yes'):
        profile_data["semi-differentiated_days"] = []
        for w in range(parameters["desired_weeks"]):
            for d in range(len(days)):
                profile_data["semi-differentiated_days"].extend(get_profile(event_data['weekday_' + str(d)]['event_starts'][w], event_data['weekday_' + str(d)]['event_volumes'][w], event_data['weekday_' + str(d)]['event_flow_rates'][w]))
    if(parameters["undifferentiated_days"] == 'yes'):
        profile_data["undifferentiated_days"] = []
        for w in range(parameters["desired_weeks"]):
            for d in range(7):
                profile_data["undifferentiated_days"].extend(get_profile(event_data['all_' + str(d)]['event_starts'][w], event_data['all_' + str(d)]['event_volumes'][w], event_data['all_' + str(d)]['event_flow_rates'][w]))
    return profile_data
                
def get_profile(event_starts, event_volumes, event_flow_rates):
    day_profile = [0]*1440
    for i in range(len(event_starts)):
        if(parameters["impulse_usages"] == 1):event_flow_rates[i] = 9999999
        if(event_flow_rates[i] < 0.5):event_flow_rates[i] = 0.5    
        duration = int(event_volumes[i]/event_flow_rates[i])
        if(parameters["mode"] == 'conservative'):
            real_event_start = event_starts[i]
        else:
            real_event_start = event_starts[i] - int(duration/2)
        remainder = event_volumes[i]%event_flow_rates[i]
        if(real_event_start + duration > 1438):
            shift_event = (real_event_start + duration) - 1438
            real_event_start -= shift_event
        for d in range(duration):
            day_profile[real_event_start + d] += event_flow_rates[i]
        if(remainder > 0):
            day_profile[real_event_start + duration] += remainder
    return day_profile

    
def save_profiles(profile_data, ewh_id):
    save_dict = {}
    if(parameters["differentiated_days"] == 'yes'):
        for s in range(len(seasons)):
            save_dict[seasons[s] + '[differentiated_days]'] = profile_data[seasons[s]]["differentiated_days"]
    if(parameters["semi-differentiated_days"] == 'yes'):
        for s in range(len(seasons)):
            save_dict[seasons[s] + '[semi-differentiated_days]'] = profile_data[seasons[s]]["semi-differentiated_days"]
    if(parameters["undifferentiated_days"] == 'yes'):
        for s in range(len(seasons)):
            save_dict[seasons[s] + '[undifferentiated_days]'] = profile_data[seasons[s]]["undifferentiated_days"]
    df = pd.DataFrame(save_dict)
    df.to_csv(save_directory_part1 + str(ewh_id) + save_directory_part2, index=False)

# %% ../nbs/00_core.ipynb 6
#######################################################################

print('Reading Source Data...')
source_data = {}
for q in EWH_RANGE:
    source_data[q] = get_source_data(q)

#######################################################################

print('Extracting Flow Data...')
flow_data = {}
for q in EWH_RANGE:
    flow_data[q] = {}
    for s in range(len(seasons)):
        flow_data[q][seasons[s]] = get_flow_data(source_data[q][seasons[s]])

#######################################################################

print('Clustering Data...')
cluster_data = {}
for q in EWH_RANGE:
    cluster_data[q] = {}
    for s in range(len(seasons)):
        cluster_data[q][seasons[s]] = get_cluster_data(flow_data[q][seasons[s]])

#######################################################################

print('Generating Events...')
event_data = {}
for q in EWH_RANGE:
    event_data[q] = {}
    for s in range(len(seasons)):
        event_data[q][seasons[s]] = get_event_data(cluster_data[q][seasons[s]])

#######################################################################

print('Building Schedules...')
profile_data = {}
for q in EWH_RANGE:
    profile_data[q] = {}
    for s in range(len(seasons)):
        profile_data[q][seasons[s]] = get_profile_data(event_data[q][seasons[s]])

#######################################################################

print('Saving Profiles...')
for q in EWH_RANGE:
    save_profiles(profile_data[q], q)
print('Finished!')

#######################################################################
