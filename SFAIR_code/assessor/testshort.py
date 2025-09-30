import os
import fnmatch

file_names=['Gloria_Macapagal_Arroyo_0002.jpg', 'Gloria_Macapagal_Arroyo_0003.jpg', 'Sandra_Bullock_0002.jpg', 'Gwyneth_Paltrow_0005.jpg', 'Gloria_Macapagal_Arroyo_0004.jpg', 'Sandra_Bullock_0001.jpg', 'Gwyneth_Paltrow_0001.jpg', 'Laura_Bush_0018.jpg', 'Gwyneth_Paltrow_0004.jpg', 'Gwyneth_Paltrow_0002.jpg', 'Vicente_Fox_0010.jpg', 'Vicente_Fox_0007.jpg', 'Vicente_Fox_0013.jpg', 'Vicente_Fox_0012.jpg', 'Vicente_Fox_0015.jpg', 'James_Blake_0001.jpg', 'Vicente_Fox_0001.jpg', 'Aaron_Eckhart_0001.jpg', 'Vicente_Fox_0008.jpg', 'Vicente_Fox_0014.jpg', 'Sandra_Bullock_0002.jpg', 'Gwyneth_Paltrow_0005.jpg', 'Gloria_Macapagal_Arroyo_0019.jpg', 'Sophia_Loren_0001.jpg', 'Gloria_Macapagal_Arroyo_0004.jpg', 'Gwyneth_Paltrow_0001.jpg', 'Laura_Bush_0041.jpg', 'Gwyneth_Paltrow_0003.jpg', 'Gloria_Macapagal_Arroyo_0003.jpg', 'Gwyneth_Paltrow_0002.jpg', 'Vicente_Fox_0014.jpg', 'Vicente_Fox_0004.jpg', 'Vicente_Fox_0005.jpg', 'Vicente_Fox_0015.jpg', 'James_Blake_0001.jpg', 'Vicente_Fox_0010.jpg', 'Vicente_Fox_0001.jpg', 'Vicente_Fox_0008.jpg', 'Aaron_Eckhart_0001.jpg', 'Vicente_Fox_0002.jpg']


def preprocess_file_extension(file_name, extension='.jpg'):
    if file_name.endswith(extension):
        return os.path.splitext(file_name)[0]
    return file_name

def find_pertubed_files():
    files_list = []
    for root, dirs, files in os.walk('input/robustness/perturbed'):
        for each in files:
            files_list.append(os.path.join(root,each))
    # print('root', root)
    # print('dirs', dirs)
    # print('files_list', files_list)
    return files_list

def find_corresponding_file(filename):
    # print("input filename = ", filename)
    filename=preprocess_file_extension(filename,extension='.jpg')
    
    # print('file name', filename)
    perturbed_files = find_pertubed_files()
    
    # print(perturbed_files)
    pert_file = ''
    for each in perturbed_files:
        # print(each.split('/')[-1])
        if (each.split('/')[-1]).startswith(filename):
            pert_file = each
            break
    # print("pert_name: ", pert_file)

    return pert_file
            
        

# def find_corresponding_file(filename):
#     #print(filename)
#     filename=preprocess_file_extension(filename,extension='.jpg')
#     #print('file name', filename)
#     pert_file = ''
#     for root, dirs, files in os.walk('./perturbed/'):
#         #print('Files',files)
#         for file in files:
#             if file.startswith(filename):  # match 3 files
#                 if file.endswith('Epsilon=0.100.jpg'):
# 	                pert_file=(os.path.join(root, file))
# 	                #print(pert_file)
# 	                return pert_file


# Example usage:
#print(file_names)

if __name__ == "__main__":
    x=[]
    # find_pertubed_files()

    for filename in file_names:
        print(filename)
        # find_corresponding_file(filename)
        x.append(find_corresponding_file(filename))
    print(x)

    
    
