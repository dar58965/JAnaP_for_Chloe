# TODO: Deprecate File


def get_experiment_date(filename):
    # TODO: Deprecate
    clean_filename = filename.strip()
    year = clean_filename[0:2]
    month = clean_filename[2:4]
    day = clean_filename[4:6]

    if year != "16":
        return ""
    else:
        return "20" + year + "-" + month + "-" + day

def get_experiment_name(filename):
    # TODO: Deprecate
    if "1 kPa" in filename and "Supp" in filename:
        return "1 Supp"
    elif "1 kPa" in filename:
        return "1"
    elif "5 kPa" in filename and "Supp" in filename:
        return "5 Supp"
    elif "5 kPa" in filename:
        return "5"
    elif "13 kPa" in filename and "Supp" in filename:
        return "13 Supp"
    elif "13 kPa" in filename:
        return "13"
    elif "280 kPa" in filename and "Supp" in filename:
        return "280 Supp"
    elif "280 kPa" in filename:
        return "280"

    elif "Glass - Supp" in filename:
        return "Glass"
    elif "Glass + Supp" in filename:
        return "Glass Supp"
    elif "Glass + cAMP" in filename:
        return "Glass Supp"


    elif "- cAMP" in filename and "DMSO" in filename:
        return "DMSO"
    elif "+ cAMP" in filename and "DMSO" in filename:
        return "DMSO Supp"
    elif "- cAMP" in filename and "Blebb" in filename and "50 uM" in filename:
        return "50 Blebb"
    elif "+ cAMP" in filename and "Blebb" in filename and "50 uM" in filename:
        return "50 Blebb Supp"

    elif "- cAMP" in filename and "Blebb" in filename and "100 uM" in filename:
        return "100 Blebb"
    elif "+ cAMP" in filename and "Blebb" in filename and "100 uM" in filename:
        return "100 Blebb Supp"

    elif "1 kPa Calyculin" in filename:
        return "1 Caly"
    elif "13 kPa DMSO" in filename:
        return "13 DMSO"
    elif "13 kPa Calyculin" in filename:
        return "13 Caly"
    elif "280 kPa DMSO" in filename:
        return "280 DMSO"
    elif "280 kPa Calyculin" in filename:
        return "280 Caly"

    elif "Glass DMSO" in filename:
        return "Glass DMSO"
    elif "Glass Calyculin" in filename:
        return "Glass Caly"

    elif "Glass" in filename:
        return "Glass"


    else:
        return ""
