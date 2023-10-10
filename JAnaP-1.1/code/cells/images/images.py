import os
import glob
import experiment

def get_dimension_date_parse(filename):
    clean_filename = filename.strip()
    year = clean_filename[0:2]
    month = clean_filename[2:4]
    day = clean_filename[4:6]

    if year != "16":
        return ""
    else:
        return "20" + year + "-" + month + "-" + day

def get_dimension_string_match(filename, data):

    for match_candidate in data:
        tokens = match_candidate.get("tokens", [])

        match = True
        for token in tokens:
            if token not in filename:
                match = False

        if match:
            return match_candidate.get("value")

    return ""


def get_image_list(images_directory):
    image_list = []

    images_directory_glob = images_directory
    if images_directory_glob[-1] != os.sep:
        images_directory_glob = images_directory_glob + os.sep
    images_directory_glob = images_directory_glob + "*"

    for image_file in glob.glob(images_directory_glob):
        file_name = os.path.basename(image_file)

        image_list.append(file_name)

    return image_list




def get_image_collection(images_directory, variant, dimensions):
    """

    Stains are variants, basically versions of the same image, that can be 
    extracted from the image name.
        variant = {
            "name": "",
            "values": [],
            "primary_value": ""
        }

    Dimensions are analytical variables that can be extracted from the image 
    name. 
        dimensions = [
            "name": {
                "type": ("String Match", "Date Parse")
                "data": []
            }

            {
                "name": "",
                "type": "", ("match", "function"),
                "data": object ("match" => {"": [], "": [], ...}, "function" => "function_name") (OrderedDict)
            },
            {
                ...
            },
            ...
        ]
    
    Returns: 
        [
            {
                "file_name": file_name,
                "file_root": image_root,
                "stain": stain,
                "experiment_name": experiment_name,
                "experiment_date": experiment_date,
                "seed_source_image": seed_source_image,

                "variant": image_stain,
                "dimensions": image_dimensions

            }
        ]

    """
    
    stains = variant.get("values", [])
    primary_stain = variant.get("primary_value", None) 

    image_data = []

    images_directory_glob = images_directory
    if images_directory_glob[-1] != os.sep:
        images_directory_glob = images_directory_glob + os.sep
    images_directory_glob = images_directory_glob + "*"

    for image_file in glob.glob(images_directory_glob):
        file_name = os.path.basename(image_file)

        image_stain = None
        image_root = file_name
        for stain in stains:
            image_root = image_root.replace(stain, "")
            if stain in file_name:
                image_stain = stain

        image_dimensions = {}

        for key, value in dimensions.iteritems():
            if value["type"] == "String Match":
                image_dimensions[key] = \
                    get_dimension_string_match(file_name, value.get("data", []))
            elif value["type"] == "Date Parse":
                image_dimensions[key] = get_dimension_date_parse(file_name)

        experiment_name = experiment.get_experiment_name(file_name)
        experiment_date = experiment.get_experiment_date(file_name)

        seed_source_image = file_name
        if primary_stain not in seed_source_image and primary_stain is not None:
            for stain in stains:
                seed_source_image = seed_source_image.replace(stain, primary_stain)
                
        image_data.append({
            "file_name": file_name,
            "file_root": image_root,
            "stain": image_stain, # TODO: Deprecate
            "experiment_name": experiment_name, # TODO: Deprecate
            "experiment_date": experiment_date, # TODO: Deprecate
            "seed_source_image": seed_source_image,
            "variant": image_stain,
            "dimensions": image_dimensions
        })

    return image_data
