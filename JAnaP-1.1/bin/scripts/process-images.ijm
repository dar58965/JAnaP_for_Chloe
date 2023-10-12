args = split(getArgument(), " ");

input_folder = args[0]
output_folder = args[1]

extension = ".tif";
setBatchMode(true);
n = 0;
processFolder(input_folder);

function processFolder(input_folder) {
 list = getFileList(input_folder);
 for (i=0; i<list.length; i++) {
      if (endsWith(list[i], "/"))
          processFolder(input_folder+list[i]);
      else if (endsWith(list[i], extension))
         processImage(input_folder, list[i]);
  }
}

function processImage(input_folder, name) {
 open(input_folder+name);
 print(n++, name);
 run("Subtract Background...", "rolling=5");
 saveAs(extension, output_folder+name);
 close();
}

