import time
import cells.application
import cells.image

import cells.aa_project
import cells.aa_waypoints

from options import OPTYPE_APPLICATION, OPTYPE_PROJECT, \
                    APPLICATION_PROJECT_LIST




def __route_cli_application_operation(options, args):
    project_headers = cells.application.get_project_headers()

    operation_type = options.operation[1]

    if operation_type == APPLICATION_PROJECT_LIST[1]:
        print "  Current Projects:"
        for key, value in project_headers.iteritems():
            print ("    => %s" % key)



def __route_cli_project_operation(options, args):
    project_headers = cells.application.get_project_headers()

    if options.project is None:
        raise Exception("You must specify a project")

    project_header = project_headers.get(options.project)

    if project_header is None:
        raise Exception("Unknown project: %s" % options.project)

    # Load project object
    project_directory = project_header.get("directory")
    project = cells.aa_project.load_project(project_directory)

    # Create any missing project directories
    cells.aa_project.create_missing_directories(project)

    operation_type = options.operation[1]

    #if operation_type == APPLICATION_PROJECT_LIST[1]:
    #    print "  Current Projects:"
    #    for key, value in project_headers.iteritems():
    #        print ("    => %s" % key)
    cell_data = cells.aa_project.generate_plan(project)


    #for cell_data_row in cell_data:
    for cell_row_idx in range(0, len(cell_data)):
        print ("Cell %s/%s - Start: %s" % (str(cell_row_idx + 1), str(len(cell_data)), str(time.time())))
        cell_data_row = cell_data[cell_row_idx]

        print ("  Loading Images - Start: %s" % (str(time.time())))
        start = time.time()
        # Get Images
        (image_original, image_processed, image_binary, image_cost) = \
            cells.image.get_images(project, cell_data_row)
        print ("                   Done: %ss elapsed" % (str(time.time() - start)))


        # Get Waypoints
        # TODO: Refactor this
        print ("  Loading Waypoints - Start: %s" % (str(time.time())))
        waypoints = cells.aa_project.cache.get_waypoints(project, cell_data_row)
        if waypoints is None:
            print ("    Calculating Waypoints - Start: %s" % (str(time.time())))
            start = time.time()

            sentry = cell_data_row.get("sentry_r"), cell_data_row.get("sentry_c")
            waypoints = cells.aa_waypoints.get_waypoints(image_processed,
                                                         image_binary,
                                                         sentry)

            print ("                            Done Computing: %ss elapsed" % (str(start - time.time())))
            # cells.aa_project.cache.cache_waypoints(project, cell_data_row, waypoints)
            print ("                            Cached:  %ss elapsed" % (str(start - time.time())))
        print ("          Waypoint count: %s" % (str(len(waypoints))))

        perimeter_path = cells.aa_waypoints.get_perimeter(image_cost, waypoints)

        from matplotlib import pyplot
        plotter = image_binary.copy()
        for e in perimeter_path:
            r, c = e
            plotter[r,c] = 5
        for e in waypoints:
            r, c = e
            plotter[r, c] = 10
        pyplot.imshow(plotter)
        output_path = "/projects/temp/umd-cells/"
        pyplot.savefig(output_path + 'path-' + str(cell_data_row["cell_id"]) + ".png",
                       dpi=300)
        pyplot.clf()



        if cell_row_idx > 20:
            break

    #

    #print len(cell_data)


def route_cli_operation(options, args):
    if options.operation[0] == OPTYPE_APPLICATION:
        __route_cli_application_operation(options, args)

    if options.operation[0] == OPTYPE_PROJECT:
        __route_cli_project_operation(options, args)