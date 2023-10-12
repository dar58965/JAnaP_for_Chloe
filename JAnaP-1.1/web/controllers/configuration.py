import configparser
import sys
import os
import shutil



class NodeConfiguration():
    class Paths():
        pass

    
def parse_config_file(config_file):
    config = configparser.ConfigParser()
    config._interpolation = configparser.ExtendedInterpolation()
    config.read(config_file)
    print "config_file read into parse..."
    
    config_file_path = os.path.dirname(config_file)
    
    paths = config['paths']
    
    for key, raw_path in paths.iteritems():
        # Paths in the configuration file are relative to the file itself
        raw_full_path = os.path.join(config_file_path, raw_path)
        # Convert to an actual path (fixes parsing issues with "//" for example)
        raw_abs_path = os.path.abspath(raw_full_path)
        # Add trailing slash
        directory = os.path.join(raw_abs_path, "")
        # Assign class variable
        setattr(NodeConfiguration.Paths, key, directory)

        print("{0}: {1}".format(key, directory))  # Print the determined directory path
        
        if not os.path.exists(directory):
            print("{0} does not exist".format(directory))
        elif os.path.isfile(directory):
            print("{0} is a file".format(directory))
        elif os.path.isdir(directory):
            print("{0} is a directory".format(directory))
        else:
            print("{0} is neither a file nor a directory".format(directory))

        if not os.path.isdir(directory):
            os.makedirs(directory)

    
