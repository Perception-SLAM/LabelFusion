# This script reads all of the files in ./train/
# that are saved in our CORL17 format
# and outputs a file that lists all files formatted
# for SegNet
#
###  Input: a subdirectories ./train/ and ./test/ with *rgb.png and *labels.png files (generated by preceding CORL17 pipeline)
###  Output: a pair of .txt files list all *.rgb and *.labels pairs (for SegNet training and testing)

import os
import yaml
import sys


OBJECTS_TO_FILTER         = ['drill']
MAX_PER_SCENE             = 10
DOWNSAMPLE_RATE           = 100    # specify in Hz, 30 Hz is sensor rate


list_specific = None

# ------------------------------
path_to_spartan  = os.environ['SPARTAN_SOURCE_DIR']
path_to_data     = path_to_spartan + "/src/CorlDev/data"
path_to_output   = os.getcwd() + "/training_set_list.txt"


# parse argument for list_specific
if len(sys.argv) > 1:
    list_specific = []
    path_to_output = os.getcwd() + "/" + sys.argv[1] + ".imglist.txt"
    with open(sys.argv[1]) as f:
        content = f.readlines()
    content = [x.strip() for x in content]
    for index, scene in enumerate(content):
        list_specific.append(scene)


# folders in /data/logs to track
folders = ["logs_test", "logs_stable"]

global_counter = 0

def recordObjects(fullpath):
    list_of_objects = []
    if os.path.isfile(fullpath):
        f = open(fullpath)
        dataMap = yaml.safe_load(f)
        for k in sorted(dataMap):
            list_of_objects.append(k)
    return list_of_objects


def WritePairToFile(rgb_file_name, labels_file_name, target):
	target.write(rgb_file_name)
	target.write(" ")
	target.write(labels_file_name)
	target.write("\n")

def addToDatasetList(fullpath_resized_images, target):
    global global_counter
    num_added_this_scene = 0

    rgb_match = ""
    labels_match = ""

    for root, dirs, files in os.walk(fullpath_resized_images):
        downsampler = 0
        for filename in sorted(files):
            if filename.endswith("labels.png") and not filename.endswith("color_labels.png"):
                labels_match = filename
                downsampler += 1
                continue

            if downsampler < DOWNSAMPLE_RATE:
                continue

            downsampler = 0

            if filename.endswith("rgb.png"):
                rgb_match = filename
                
            if rgb_match.split("_")[0] == labels_match.split("_")[0]:
                rgb_split = rgb_match.split("_")
                if len(rgb_split)>1 and rgb_split[1] == "rgb.png":
                    WritePairToFile(os.path.join(root, rgb_match), os.path.join(root, labels_match), target)
                    global_counter += 1
                    rgb_match = ""
                    labels_match = ""
                    num_added_this_scene += 1
                    if num_added_this_scene >= MAX_PER_SCENE:
                        return


def crawlDirectories(path_to_data, path_to_output):
    target = open(path_to_output, 'w')
    
    for folder in folders:
        path_to_folder = path_to_data + "/" + folder 
        for subdir, dirs, files in os.walk(path_to_folder):
            for dir in sorted(dirs):
                if list_specific is not None:
                    print "I have a certain list"
                    if dir not in list_specific:
                        continue
                fullpath = os.path.join(subdir, dir)
                path_after_data =  os.path.relpath(fullpath, path_to_data)
                objects = recordObjects(os.path.join(fullpath, "registration_result.yaml"))
                
                for object_to_filer in OBJECTS_TO_FILTER:
                    if object_to_filer in objects:
                        #print "found", object_to_filer, "in", fullpath
                        print dir
                        addToDatasetList(fullpath+"/resized_images/", target)

            break # don't want recursive walk

    target.close()


crawlDirectories(path_to_data, path_to_output)

print "Made a list of ", global_counter, " training set pairs"