import ast
import socket
import numpy as np
import json
from flask import jsonify
import os
import random
import time
import sys
import platform
import subprocess
from datetime import datetime
import requests
from scipy.spatial.distance import jensenshannon
from secureconnect import make_request

url = 'http://10.16.123.112:5010/'
monitor_port = int('5010')
#no slashes no http in monitor_host or gives error
monitor_host = "10.16.123.112"
local_url = 'http://127.0.0.1:5000/'
remote_url = 'http://10.16.123.112:5001/'

recent_masks = []
initial_input = {}
recent_input = {}
save_path = "output/"
ground_truth_path = "testcases_index.json"
model_path = "../model_deploy/app/local/gender_detection.h5"
context_path = "opt_context/"
integrity_path = "selfreplacement_test_results/"
test_times = 0




class AIProperty:
    def __init__(self, name, num1, num2, flag):
        self.name = name  # name of the property
        self.dataset_number = num1  # number of datasets to choose input from
        self.input_number = num2  # number of input instances from each dataset
        self.input_flag = flag  # flag of the input to use the same as before or randomized

def test_scheduler(t_max, properties, threshold, time_limit):
    """
    Invoke test at random time spot
    :param t_max: the max time interval, the unit is hour
    :param properties: the property class list to test
    :param threshold: the threshold dictionary for property
    :return: None
    """
    global test_times
    t_max_seconds = t_max * 60 * 60

    while True:
        random_delay = random.uniform(0, t_max_seconds)
        #print("Time delay: ", random_delay)

        time.sleep(random_delay)
        #start_time = datetime.now()
        start_time = time.time()
        print('This is the start time: ',start_time)
        if test_identity(properties[0], threshold):
            local_results, remote_results, ground_truth = test_dispatcher(properties[1:])
            test_times += 1

            result_score_local, result_score_remote = result_accumulator(local_results, remote_results, ground_truth,
                                                                     time_limit)
            test_property_preservation(result_score_local, result_score_remote, threshold)
        
        #notes end time, deducts  start time from it and gives the duration of the test.
        #end_time = datetime.now()
        end_time = time.time()
        print('Ending Self-replacement test ....')	
        print('This is the end time: ',end_time)
    
       
        time_difference = end_time -start_time
        print("Execution time of program is: ", time_difference, "s")
def test_identity (identity_property, threshold):
    selected_files = select_random_input(identity_property.name,identity_property.dataset_number,identity_property.input_number)

    local_results = send_test_request(selected_files, 0)
    remote_results = send_test_request(selected_files, 1)
    ground_truth = generate_ground_truth(selected_files)

    result_score_local = result_transfer_identity(local_results)
    result_score_remote = result_transfer_identity(remote_results)

    js_distance = calculate_dissimilarity(result_score_local, result_score_remote, threshold)
    
    if js_distance <= threshold['identity']:
        return True
    else:
        print("Identity violation! Jensen-Shannon distance =",js_distance)
        return False

def calculate_dissimilarity(result_t1, result_t2, threshold):
    """
    calculate the value of dissimilarity
    :param result_t1: first result
    :param result_t2: second result
    :param threshold: the threshold
    :return: value of dissimilarity
    """
    if len(result_t1) != len(result_t2):
        raise ValueError("Input strings must have the same length")
    #print(type(result_t1))
    #print(result_t1)
    
    # todo: calculate KL Divergence using signatures for the local and remote AI
    signature_local= np.array(result_t1)
    signature_remote= np.array(result_t2)
    
    signature_local = signature_local / np.sum(signature_local)
    signature_remote = signature_remote / np.sum(signature_remote)

    #Calculate Jensen-Shannon distnace to test if the two distributions are different    
    js_distance = jensenshannon(signature_local, signature_remote)
    
           
    #if js-distance is more than threshold remote AI has lost its operational identity
    if js_distance > threshold['identity']:
        print("Alert: Identity violation! Jensen-Shannon distance = ", js_distance)
    else:
        print("Note: Identity preserved.")

    return js_distance


def concat_results(result):
    """
    concatenate the result dictionary
    :param result: the result dictionary
    :return: binary format result dictionary
    """
    # Keep only 10 decimal numbers for each value
    trimmed_dict = {key: [[round(num, 10) for num in sublist] for sublist in value] for key, value in
                    result.items()}

    # Remove negative symbols and dots from the numbers
    cleaned_dict = {
        key: [[''.join(char for char in str(abs(num * 10)) if char.isdigit()) for num in sublist] for sublist in value]
        for key, value in trimmed_dict.items()}

    # Concatenate the numbers for each key into a single string
    concatenated_dict = {key: [''.join(map(str, sublist)) for sublist in value] for key, value in cleaned_dict.items()}

    # Join the strings for each key
    final_dict = {key: ''.join(value) for key, value in concatenated_dict.items()}

    # Convert strings to binary numbers
    binary_dict = {key: bin(int(value))[2:] for key, value in final_dict.items()}

    return binary_dict

#here we need to pass the ground-truth to determine if the test passed.
def test_property_preservation(results_dict1, results_dict2, threshold_values):
    """
    test property preservation
    :param results_dict1: result from t1
    :param results_dict2: result from t2
    :param threshold_values: property threshold dictionary
    :return: None
    """
    test_Score_values = {}

    #print("Calculating test score...")

    for key in results_dict1:
        if key in results_dict2 and key in threshold_values:
            value1 = results_dict1[key]
            value2 = results_dict2[key]
            threshold = threshold_values[key]
            
            if key !='fairness' and key!='identity':
                print(f"Key: {key}, Local AI Test Score: {value1}, Remote AI Test Score: {value2}, threshold: {threshold}")

            if key == 'identity':
                test_Score_values[key] = calculate_dissimilarity(value1, value2, threshold)
            else:
                test_Score_values[key] = abs(value1 - value2)
                if test_Score_values[key] > threshold:
                    print(f"Alert: {key} violation! Dissimilarity value = {test_Score_values[key]}")
                else:
                    print(f"Note: {key} preserved.")

    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"test_result_{current_time}.json"

    filepath = os.path.join(integrity_path, filename)
    with open(filepath, 'w') as f:
        json.dump(test_Score_values, f)


def generate_mask(size, range_i, range_j):
    """
    generate random mask number and update recent_masks[]
    :param size: the amount of number to choose
    :param range_i: the randomization range start
    :param range_j: the randomization range end
    :return: mask array
    """
    global recent_masks
    new_mask = random.sample(range(range_i, range_j + 1), size)

    while new_mask in recent_masks:
        new_mask = random.sample(range(range_i, range_j + 1), size)

    recent_masks.append(new_mask)
    recent_masks = recent_masks[-10:]

    return new_mask


def select_random_input(property_name, dataset_number, input_number):
    """
    Random input generation for test
    :param property_name: property to test
    :param dataset_number: how many datasets to choose from
    :param input_number: how many input files to choose in each dataset
    :return:
    """
    global test_times
    selected_files_list = []

    input_folder = f"input/{property_name}"
    #uncomment if want to see the folder being used for input selection
    #print("Input folder path: ", input_folder)

    folder_items = os.listdir(input_folder)

    if dataset_number == 1:
        files = [file for file in folder_items if os.path.isfile(os.path.join(input_folder, file))]

        # get random files by generating mask
        random_indexes = generate_mask(input_number, 0, len(files) - 1)
        #print(random_indexes) 
        selected_files = [files[i] for i in random_indexes]

        # store the full path of input files
        for index, file_name in enumerate(selected_files):
            selected_files[index] = os.path.join(input_folder, file_name)
    else:
        # Get subfolders
        subfolders = [item for item in folder_items if os.path.isdir(os.path.join(input_folder, item))]
        if len(subfolders) != int(dataset_number):
            print("Invalid number of subfolders in input folder!")
            return None

        # Loop through the subfolders and select random files from each
        for subfolder in subfolders:
            subfolder_path = os.path.join(input_folder, subfolder)
            #uncomment to see which subfolder is being used for input file selection --
            #print(f"Subfolder path: {subfolder_path}")

            # Get the array of files in the subfolder
            files = os.listdir(subfolder_path)
            files = [file for file in files if os.path.isfile(os.path.join(subfolder_path, file))]

            # Get random files by generating mask
            random_indexes = generate_mask(int(input_number), 0, len(files) - 1)
            selected_files = [files[i] for i in random_indexes]

            # Store the full path of input files
            selected_files_list.extend(
                [os.path.join(input_folder, subfolder, file_name) for file_name in selected_files])

    # Store the input files for reproduce
    input_label = 'recent' if test_times != 0 else 'initial'
    saved_file_path = f"input_record/{input_label}_input_{property_name}.json"
    with open(saved_file_path, 'w') as json_file:
        json.dump(selected_files_list, json_file)

    #these selected files are used as ground truth. 
    #print("Selected file paths saved to:", saved_file_path)
    #uncomment the following to see the files used in test	
    #print("Selected file paths:", selected_files_list)
    return selected_files_list

#TODO: improve this function for robustness and then improve the robustness test

def select_random_input_fairness(dataset_number, input_number):
    color = ['black', 'white']
    selected_files_list = []

    for item in color:
        input_folder = f"input/fairness/{item}"
        # print("Input folder path: ", input_folder)

        folder_items = os.listdir(input_folder)

        subfolders = [item for item in folder_items if os.path.isdir(os.path.join(input_folder, item))]
        if len(subfolders) != int(dataset_number):
            print("Invalid number of subfolders in input folder!")
            return None

        # Loop through the subfolders and select random files from each
        for subfolder in subfolders:
            subfolder_path = os.path.join(input_folder, subfolder)
            # print(f"Subfolder path: {subfolder_path}")

            # Get the array of files in the subfolder
            files = os.listdir(subfolder_path)
            files = [file for file in files if os.path.isfile(os.path.join(subfolder_path, file))]

            # Get random files by generating mask
            random_indexes = generate_mask(int(input_number), 0, len(files) - 1)
            selected_files = [files[i] for i in random_indexes]

            # Store the full path of input files
            selected_files_list.extend([os.path.join(input_folder, subfolder, file_name) for file_name in selected_files])

    # Store the input files for reproduce
    input_label = 'recent' if test_times != 0 else 'initial'
    saved_file_path = f"input_record/{input_label}_input_fairness.json"
    with open(saved_file_path, 'w') as json_file:
        json.dump(selected_files_list, json_file)

    # print("Selected file paths saved to:", saved_file_path)

    # print("Selected file paths:", selected_files_list)

    return selected_files_list

# function to find related perturbed files

def preprocess_file_extension(file_name, extension='.jpg'):
    if file_name.endswith(extension):
        return os.path.splitext(file_name)[0]
    return file_name

def find_pertubed_files():
    files_list = []
    for root, dirs, files in os.walk('input/robustness/perturbed'):
        for each in files:
            files_list.append(os.path.join(root,each))
    return files_list

def find_corresponding_file(filename):
    # print(filename)
    filename = filename.split('/')[-1]
    filename=preprocess_file_extension(filename,extension='.jpg')
    # print(filename)
    perturbed_files = find_pertubed_files()
    # print(perturbed_files)
    pert_file = ''
    for each in perturbed_files:
        if (each.split('/')[-1]).startswith(filename):
            pert_file = each
            break
    # print("pert_file = ", pert_file)
    return pert_file
    
def select_random_input_robustness(dataset_number, input_number): 
    input_file_type = ['benign','perturbed']
    selected_files_list = []

    for item in input_file_type:
        input_folder = f"input/robustness/{item}"

        
        if item == 'benign':
            folder_items = os.listdir(input_folder)
            subfolders = [item for item in folder_items if os.path.isdir(os.path.join(input_folder, item))]
            #print(subfolders)
            if len(subfolders) != int(dataset_number):
                print("Invalid number of subfolders in input folder!")
                return None
            for subfolder in subfolders:
                subfolder_path = os.path.join(input_folder, subfolder)
            
                files = os.listdir(subfolder_path)
                files = [file for file in files if os.path.isfile(os.path.join(subfolder_path, file))]
                
                # Get random files by generating mask
                random_indexes = generate_mask(int(input_number), 0, len(files) - 1)
                selected_files = [files[i] for i in random_indexes]

               # Store the full path of input files
                selected_files_list.extend([os.path.join(input_folder, subfolder, file_name) for file_name in selected_files])
            #print(selected_files_list)
            # print('Test Passed')

        else:
            similar_files=[]
            for filename in selected_files_list:
                corresponding_file = find_corresponding_file(filename)
                similar_files.append(corresponding_file)            
            selected_files_list.extend(similar_files)
            
        
            
    # Store the input files for reproduce
    input_label = 'recent' if test_times != 0 else 'initial'
    saved_file_path = f"input_record/{input_label}_input_robustness.json"
    with open(saved_file_path, 'w') as json_file:
        json.dump(selected_files_list, json_file)

    # print("Selected file paths saved to:", saved_file_path)

    # print("Selected file paths:", selected_files_list)

    return selected_files_list

def reproduce_input(property_name, test_flag):
    """
    Input generation for reproduce test flag
    :param property_name: the property to test
    :param test_flag: initial input-1 or recent input-2
    :return:
    """
    input_labels = {1: 'initial', 2: 'recent'}
    input_label = input_labels.get(test_flag)

    if input_label is None:
        print("Invalid test flag! It must be 1 or 2.")
        return None

    saved_file_path = f"input_record/{input_label}_input_{property_name}.json"
    with open(saved_file_path, 'r') as json_file:
        selected_files_list = json.load(json_file)
    return selected_files_list


def send_test_request(files, model_flag):
    """
    Send test request to the model server
    :param files: test input files
    :param model_flag: remote-1 or local-0
    :return: test result array
    """
    results_array = []

    if model_flag == 0:
        for file in files:
            with open(file, 'rb') as file_obj:
                resp = requests.post(local_url+"predict_local",
                                     files={'image': file_obj})
                results_array.append(ast.literal_eval(resp.text))
    elif model_flag == 1:
        for file in files:
            with open(file, 'rb') as file_obj:
                resp = requests.post(remote_url+"predict_remote",
                                     files={'image': file_obj})
                results_array.append(ast.literal_eval(resp.text))
                
    else:
        print("Invalid model flag! Must be 0 for local or 1 for remote.")
        return None

    return results_array


def send_test_request_efficiency(files, model_flag):
    """
    Send test request to the model server
    :param files: test input files
    :param model_flag: remote-1 or local-0
    :return: test result array
    """
    time_array = []

    if model_flag == 0:
        for file in files:
            start_time = time.perf_counter()
            with open(file, 'rb') as file_obj:
                requests.post(local_url+"predict_local",
                              files={'image': file_obj})
            end_time = time.perf_counter()
            time_array.append(end_time - start_time)
    elif model_flag == 1:
        for file in files:
            start_time = time.perf_counter()
            with open(file, 'rb') as file_obj:
                requests.post(remote_url+"predict_remote",
                              files={'image': file_obj})
            end_time = time.perf_counter()
            time_array.append(end_time - start_time)
    else:
        print("Invalid model flag! Must be 0 for local or 1 for remote.")
        return None

    return time_array


def send_test_request_robustness(files, model_flag):
    """
    Send test request to the model server, invoke monitor to
    :param files: test input files
    :param model_flag: remote-1 or local-0
    :return: test result array
    """
    results_array = []
    directory = context_path

    if model_flag == 0:
        collect_opt_context()

        for file in files:
            with open(file, 'rb') as file_obj:
                resp = requests.post(local_url+"predict_local",
                                     files={'image': file_obj})
                results_array.append(ast.literal_eval(resp.text))
    elif model_flag == 1:

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((monitor_host, 5010))
        client_socket.send(b"Test Robustness")

        current_time = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"remote_opt_context_{current_time}.json"
        filepath = os.path.join(directory, "remote", filename)

        with open(filepath, "wb") as file:
            while True:
                file_data = client_socket.recv(1024)
                if not file_data:
                    break
                file.write(file_data)

        #print(f"Operational context of remote AI saved in remote_opt_context_{current_time}.json")

        client_socket.close()

        for file in files:
            with open(file, 'rb') as file_obj:
                resp = requests.post(remote_url+"predict_remote",
                                     files={'image': file_obj})
                results_array.append(ast.literal_eval(resp.text))
    else:
        print("Invalid model flag! Must be 0 for local or 1 for remote.")
        return None
    #print(results_array)
    return results_array


def get_system_info():
    system_info = {}
    system_info['os_version'] = platform.platform()
    system_info['python_version'] = platform.python_version()
    try:
        flask_version = subprocess.check_output(['pip', 'show', 'Flask']).decode().split('\n')[1].split(': ')[1]
        system_info['flask_version'] = flask_version
    except Exception as e:
        print(f"Error retrieving Flask version: {e}")
        system_info['flask_version'] = "Unknown"
    return system_info


def collect_opt_context():
    directory = context_path

    system_info = get_system_info()

    if system_info:
        data = {'os_version': system_info['os_version'],
                'python_version': system_info['python_version'],
                'flask_version': system_info['flask_version']
                }

        current_time = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"local_opt_context_{current_time}.json"
        filepath = os.path.join(directory, "local", filename)

        with open(filepath, "w") as json_file:
            json.dump(data, json_file, indent=4)

        #print(f"Operational context of remote AI saved in local_opt_context_{current_time}.json")


def generate_ground_truth(files):
    labels = []
    global ground_truth_path
    
    with open(ground_truth_path, 'r') as json_file:
        ground_truth = json.load(json_file)

    
    for file_path in files:
        label = ground_truth.get(file_path)
        
        labels.append(label)

    #print("Ground truth: ", labels)
    return labels


def test_dispatcher(property_list):
    """
    select input files according to mask, send requests to model, store results
    :param property_list: properties to test with requirement
    :return: test results dictionary
    """
    results_dict_local = {}
    results_dict_remote = {}
    ground_truth = {}

    # Test one property at each time
    for item in property_list:
        #changed it because 50 is from one folder
        #print(f"Testing {item.name} with dataset_number = {item.dataset_number}, "
        print(f"Testing {item.name}, "
              f"Number of test cases = {str(int(item.input_number)*2)}, input_flag = {item.input_flag}.")
        if item.dataset_number == '0':
            print("Error: invalid dataset number!")
            return None

        if item.input_flag == '0':
            if item.name == 'fairness':
                selected_files = select_random_input_fairness(item.dataset_number, item.input_number)             
                #print("faireness selected_files:", selected_files)
            elif item.name =='robustness':
                selected_files = select_random_input_robustness(item.dataset_number, item.input_number) 
            else:
                selected_files = select_random_input(item.name, item.dataset_number, item.input_number)
        else:
            selected_files = reproduce_input(item.name, item.input_flag)

        # Store the result in dictionary with property name as key
        if item.name == 'efficiency':
            results_dict_local[item.name] = send_test_request_efficiency(selected_files, 0)
            results_dict_remote[item.name] = send_test_request_efficiency(selected_files, 1)
        elif item.name == 'robustness':
            results_dict_local[item.name] = send_test_request_robustness(selected_files, 0)
            results_dict_remote[item.name] = send_test_request_robustness(selected_files, 1)
        else:
            results_dict_local[item.name] = send_test_request(selected_files, 0)
            results_dict_remote[item.name] = send_test_request(selected_files, 1)
            
        ground_truth[item.name] = generate_ground_truth(selected_files)
    #print("Results from local AI tests:", results_dict_local)
    #print("Results from remote AI tests:", results_dict_local)
    return results_dict_local, results_dict_remote, ground_truth

# this function needs to improve
def result_transfer_identity(results_list):  # [[x1, y1], [x2, y2], [...]] \Test
    signature_number = ""
    signatures_list=[]
    #print(results_list)
    #print(len(results_list))	
    for numbers in results_list:
        try:
            numbers = [float(num) for num in numbers]
            
        except ValueError:
            continue
	    
        chosen_number = max(numbers)
        
        signatures_list.append(chosen_number)
        

    return signatures_list

# EFFICIENCY 
def result_transfer_efficiency(result_list, time_threshold):
    score_result = 0
    time_threshold = 0.2
    for time_taken in result_list:
        #WRONG IF 
        #print(time_taken)
        if time_taken < time_threshold:
            score_result += 1

    #print(score_result)
    return score_result


def result_transfer_fairness(results_list, ground_truth):
    binary_result = []
    first_score = 0
    second_score = 0
    #print('This is test ground truth',ground_truth)
    for result in results_list:
        # Append 0 if the first number is larger or equal, otherwise append 1
        bigger_index = np.argmax(result)
        binary_result.append(0 if bigger_index == 0 else 1)
        
    #
    #test if the length of results list matches corresponding ground truth list
    if len(binary_result) != len(ground_truth):
        return "Result are not of the same length as ground truth!"

    mid_results = len(results_list) // 2
    
    # Iterate through the lists and calculate scores
    for i in range(len(results_list)):
        if i < mid_results:
            #print('This is a local test',binary_result[i], ground_truth[i])
            if binary_result[i] == ground_truth[i]:
                first_score += 1

        else:
            #print('This is a remote test',binary_result[i], ground_truth[i])
            if binary_result[i] == ground_truth[i]:
                second_score += 1
    #print(first_score) returns zero
    print(f"Fairness: black people score = {first_score}, white people score = {second_score}, Discimination Value = {abs(first_score - second_score)}")
    return abs(first_score - second_score)

def result_transfer_robustness(results_list, ground_truth):
    binary_result = []
    first_score = 0
    second_score = 0
    #print('This is test ground truth',ground_truth)
    for result in results_list:
        # Append 0 if the first number is larger or equal, otherwise append 1
        bigger_index = np.argmax(result)
        binary_result.append(0 if bigger_index == 0 else 1)
        
    #
    #test if the length of results list matches corresponding ground truth list
    if len(binary_result) != len(ground_truth):
        return "Result are not of the same length as ground truth!"

    mid_results = len(results_list) // 2
    
    # Iterate through the lists and calculate scores
    for i in range(len(results_list)):
        if i < mid_results:
           # print('This is a local test',binary_result[i], ground_truth[i])
            if binary_result[i] == ground_truth[i]:
                first_score += 1

        else:
           # print('This is a remote test',binary_result[i], ground_truth[i])
            if binary_result[i] == ground_truth[i]:
                second_score += 1
    #print(first_score) returns zero
    #print(f"Robustness: Benign input score = {first_score}, Perturbed input score = {second_score}, Robustness Value = {abs(first_score - second_score)}")
    print(f"Robustness: Benign input score = {first_score}, Perturbed input score = {second_score}, Difference in performance = {((abs(first_score - second_score))/mid_results)*100},%")
    return abs(first_score - second_score)

def result_transfer_other_property(results_list, ground_truth):
    binary_result = []
    property_score = 0

    for result in results_list:
        # Append 0 if the first number is larger or equal, otherwise append 1
        bigger_index = np.argmax(result)
        binary_result.append(0 if bigger_index == 0 else 1)

    #print("binary_result: ", binary_result)

    if len(binary_result) != len(ground_truth):
        return "Result are not of the same length as ground truth!"

    # Loop through the arrays simultaneously
    for i in range(len(binary_result)):
        # Check if the value at the current index is the same in both arrays
        if binary_result[i] == ground_truth[i]:
            property_score += 1

    return property_score


"""
    transfer original result and save them to files
    :param time_threshold: the limit of success
    :param ground_truth: ground truth generated when selecting input files
    :param results_local: results of local model
    :param results_remote: results of remote model
    :return: None
    """
def result_accumulator(results_local, results_remote, ground_truth, time_threshold):
    
    transfer_result_local = {}
    transfer_result_remote = {}
    directory = save_path

    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"transferred_output_{current_time}.json"

    # transfer original local result
    for key, value in results_local.items():
        print(f"Accumulating test results for {key} of the local AI")
        if key == 'identity':
            transfer_result_local[key] = result_transfer_identity(value)
            #print("Hello Local", value)
        elif key == 'efficiency':
            transfer_result_local[key] = result_transfer_efficiency(value, time_threshold)
        elif key == 'fairness':
            #print("In function result_accumulator - ground_truth: ", ground_truth)
            transfer_result_local[key] = result_transfer_fairness(value, ground_truth[key])
        elif key == 'robustness':
            #print("In function result_accumulator - ground_truth: ", ground_truth)
            transfer_result_local[key] = result_transfer_robustness(value, ground_truth[key])
        else:
            transfer_result_local[key] = result_transfer_other_property(value, ground_truth[key])

    # transfer original remote result
    for key, value in results_remote.items():
        print(f"Accumulating test results for {key} of the remote AI")
        if key == 'identity':
            transfer_result_remote[key] = result_transfer_identity(value)
            #(print("Hello remote", value))
        elif key == 'efficiency':
            transfer_result_remote[key] = result_transfer_efficiency(value, time_threshold)
        elif key == 'fairness':
            #print('Test inaccumulator',ground_truth[key])
            transfer_result_remote[key] = result_transfer_fairness(value, ground_truth[key])
        elif key == 'robustness':
            #print("In function result_accumulator - ground_truth: ", ground_truth)
            transfer_result_local[key] = result_transfer_robustness(value, ground_truth[key])
        else:
            transfer_result_remote[key] = result_transfer_other_property(value, ground_truth[key])

    filepath = os.path.join(directory, "local", filename)
    with open(filepath, 'w') as f:
        json.dump(transfer_result_local, f)

    filepath = os.path.join(directory, "remote", filename)
    with open(filepath, 'w') as f:
        json.dump(transfer_result_remote, f)

    print("Results saved at", current_time)
    
    return transfer_result_local, transfer_result_remote
    
    
# the function that gets alerts from monitor and writes them to json file

def write_monitor_alert_to_json(host):
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"monitoralerts/monitor_alert_{current_time}.json"
    
    # Call make_request function from secureconnect module
    alert_data = make_request(host)
    
    if alert_data is None:
        print("Failed to make request or received non-200 response")
        return

    try:
        # Try to decode response content as JSON
        with open(filename, 'w') as json_file:
            json.dump(alert_data, json_file, indent=4)
        
        print(f"A new monitor alert written to {filename}")
        
    except Exception as e:
        print(f"An error occurred while writing to JSON file: {e}")


if __name__ == "__main__":
    print('Contacting monitor for changes in remote context...')
    make_request(url)
    write_monitor_alert_to_json(url)
    # the time interval between two test
    max_time_interval = 0.001

    time_threshold = 0.05

    # property to test, flag = 0 means random, flag = 1 means initial, flag = 2 means recent
    property_dict = [
        AIProperty('identity', '2', '50', '0'),
        AIProperty('correctness', '2', '50', '0'),
        AIProperty('robustness', '2', '50', '0'),
        AIProperty('fairness', '2', '50', '0'),
        AIProperty('efficiency', '2', '50', '0')
    ]

    # threshold to trigger warning message of each property
    threshold_dict = {"identity": 0, "correctness": 0, "robustness": 0, "fairness": 0.2, "efficiency": 0}

    # invoke test_scheduler
    print('Starting self replacement test...')
    #start_time = datetime.now() 
    test_scheduler(max_time_interval, property_dict, threshold_dict, time_threshold)
    
    
