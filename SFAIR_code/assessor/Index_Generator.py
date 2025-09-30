import os
import json


def scan_files(start_path):
    # Define the folders to skip
    folders_to_skip = {'old', 'new'}
    file_labels = {}

    # Walk through the directory
    for root, dirs, files in os.walk(start_path):
        # Skip the specified folders
        dirs[:] = [d for d in dirs if d not in folders_to_skip]

        # Calculate the depth of the current directory
        depth = root[len(start_path):].count(os.sep)

        print("root:", root)
        print("dirs:", dirs)
        print("files:", files)
        print("depth:", depth)

        for file in files:
            file_path = os.path.join(root, file)
            print("file_path:", file_path, "depth:", depth)

            if 'women' in os.path.basename(root):
                label = 1
            else:
                label = 0

            # If a label is set, add the file path and its label to the dictionary
            if label is not None:
                file_labels[file_path] = label

    # Write the dictionary to a file
    with open('testcases_index.json', 'w') as file:
        json.dump(file_labels, file, indent=4)


scan_files('input/')
