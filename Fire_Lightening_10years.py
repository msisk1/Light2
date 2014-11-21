""""
This code was written by ML Sisk for with with the Rocha lab at Notre Dame on lightening in Alaska
It only works with local file references Howdy
"""
import arcpy, os, timeit


# Input variables:
data_directory = "E:\\GISWork_2\\Lightening\\DataFromZach\\"
AOI_name = "Central_Alaska.shp"
lightening_name = "Lightning1986Thru2012.shp"
fire_areas_name = "FireAreaHistory.shp"

#Setable variables
FIRST_YEAR = 1984
LAST_YEAR = 2012
YEAR_GAP = 10
DAY_RANGE = 10
TOTAL_AREA = 578885.198172 #here calculated in ArcGIS, could be done programatically as well


all_years = [i for i in range(FIRST_YEAR , LAST_YEAR + 1)]
#all_years = [2005]
break_counter = -1
overwrite = False


#Field Names: PRE-EXISTING
lightening_date_field = "LOCALDATET"
fire_date_field = "DiscDate"
lightening_index_field = "OBJECTID"
fire_area_field = "AreaKM"


#Field Names: NEW
overlap_field = "overlap"
single_date_field = "singledate"

#File Path and Output Variables
output_directory = "E:\\GISWork_2\\Lightening\\Outputs\\"
fire_are_aoi_name = os.path.splitext(fire_areas_name)[0] + "_CentralAK_Only.shp"
lightening_aoi_name = os.path.splitext(lightening_name)[0] + "_CentralAK_Only.shp"
fire_areas_path = data_directory + fire_areas_name
AOI_path =  data_directory + AOI_name
lightening_path =  data_directory + lightening_name

lightening_with_all = output_directory + os.path.splitext(lightening_name)[0] + "_withAllStrikes.shp"
lightening_aoi_path = output_directory + lightening_aoi_name
fire_area_aoi_path = output_directory + fire_are_aoi_name


#TESTING INSTANCES

##lightening_path = "E:\\GISWork_2\\Lightening\\Testing\\Points.shp"
##fire_areas_path = "E:\\GISWork_2\\Lightening\\Testing\\Areas.shp"
##lightening_aoi_path = "E:\\GISWork_2\\Lightening\\Testing\\points_aoi.shp"
##fire_area_aoi_path = "E:\\GISWork_2\\Lightening\\Testing\\Areas_aoi.shp"

#END TESTING INSTANCES




#Layer Names
fire_areas_all_lyr = "all_fire_areas_layer"
AOI_lyr = "AOI_Layer"
lightening_all_lyr = "lightening_all_layer"
lightening_aoi_lyr = "lightening_aoi_layer"
fire_areas_aoi_lyr = "all_fire_aoi_layer"
lightening_with_all_lyr = "lightening_with_all_lyr"






strikes_output_file_name = "Output_Table_Strikes_{0}-{1}.csv".format(FIRST_YEAR,LAST_YEAR)
strikes_output_file_path = output_directory + strikes_output_file_name
strikes_header = "{0},{1},{2},{3},{4},{5},{6},{7}".format("Year","Strk_Total","Strk_Old","Strk_New","Strk_Outside","Strk_Before","Strk_After","Strk_Overlap")

fires_output_name = "OutputTable_Fire.csv_{0}-{1}.csv".format(FIRST_YEAR,LAST_YEAR)
fires_output_table = output_directory + fires_output_name
fires_header = "{0},{1},{2},{3},{4},{5},{6},{7}".format("year","Fire_n_new","Fire_area_new","Fire_n_old","Fire_area_old","Fire_area_noFire","Fire_n_overlap","Fire_area_overlap")


def deleteIfItExists(something, ARC):
    if ARC :
        if arcpy.Exists(something):
            arcpy.Delete_management(something)
    else :
        if os.path.exists(something):
            os.remove(something)


def preProcessing():
    print "1). Preprocessing"
    if not os.path.exists(output_directory): #Tests to see if the output directory exists, and if not, creates it
        os.makedirs(output_directory)
    all_layers = [lightening_with_all_lyr, fire_areas_all_lyr, AOI_lyr, lightening_all_lyr, lightening_aoi_lyr, fire_areas_aoi_lyr, "temp_f", "temp_l"] # Removing any preexitsting layers
    for each_layer in all_layers:
        deleteIfItExists(each_layer, True)
    if overwrite:
        print "     Overwrite on, deleting any existing previous runs"
        deleteIfItExists(lightening_aoi_path, True)
        deleteIfItExists(fire_area_aoi_path, True)
    if not arcpy.Exists(lightening_aoi_path) and not arcpy.Exists(fire_area_aoi_path):
        print "     a). creating layers within time and extent specified"
        arcpy.MakeFeatureLayer_management(fire_areas_path, fire_areas_all_lyr)
        arcpy.MakeFeatureLayer_management(AOI_path, AOI_lyr)
        arcpy.MakeFeatureLayer_management(lightening_path, lightening_all_lyr)
        print "          - making selections"
        arcpy.SelectLayerByLocation_management(fire_areas_all_lyr, "INTERSECT", AOI_lyr, "", "NEW_SELECTION")
        selc_f = "EXTRACT( YEAR FROM \"{0}\")  >= {1} AND EXTRACT( YEAR FROM \"{0}\")  <= {2}".format(fire_date_field, FIRST_YEAR - YEAR_GAP, LAST_YEAR)
        arcpy.MakeFeatureLayer_management(fire_areas_all_lyr,"temp_f",selc_f)
        arcpy.SelectLayerByLocation_management(lightening_all_lyr, "INTERSECT", AOI_lyr, "", "NEW_SELECTION")
        selc_l = "EXTRACT( YEAR FROM \"{0}\")  >= {1} AND EXTRACT( YEAR FROM \"{0}\")  <= {2}".format(lightening_date_field, FIRST_YEAR, LAST_YEAR)
        arcpy.MakeFeatureLayer_management(lightening_all_lyr,"temp_l",selc_l)
        print "          - saving features"
        arcpy.CopyFeatures_management("temp_f",fire_area_aoi_path)
        arcpy.CopyFeatures_management("temp_l",lightening_aoi_path)
        for each_layer in all_layers:
            deleteIfItExists(each_layer, True)
    else:
        print "      a). Output files exist: making layers"
    print "      b). processing strikes to flag overlap"
    if overwrite:
        deleteIfItExists(lightening_with_all)
    if not arcpy.Exists(lightening_with_all):
        buildNewOverlapFile()
    arcpy.MakeFeatureLayer_management(lightening_with_all, lightening_with_all_lyr)
    arcpy.MakeFeatureLayer_management(fire_area_aoi_path, fire_areas_aoi_lyr)
    print "      c). creating output files: {0}, {1}".format(strikes_output_file_name, fires_output_name)
    logFileWriter = open(strikes_output_file_path, 'w')
    logFileWriter.write(strikes_header + "\n")
    logFileWriter.close()



def buildNewOverlapFile():
    """
    This will create a version of the input file that contains a code for any overlap. Only needs to be done once and should take about 30 minutes
    """
    lightening_temp = output_directory + os.path.splitext(lightening_name)[0] + "_temp.shp"
    fire_intersect_file = output_directory + "fire_intersect.shp"
    lightening_with_multiples = output_directory + os.path.splitext(lightening_name)[0] + "_withMultpleStrikes.shp"
    fire_temp_file = output_directory + "fire_temp.shp"
    if not arcpy.Exists(fire_temp_file):
        arcpy.CopyFeatures_management(fire_area_aoi_path, fire_temp_file)
        fields = arcpy.ListFields(fire_temp_file) #Generating a list to delete all the extra fields
        drop_fields = []
        for f in fields :
            if f.name not in ["DiscDate","FID","Shape"]:
                drop_fields.append(str(f.name))
        print "          - Creating temporary fire instance"
        arcpy.DeleteField_management(fire_temp_file, drop_fields)
    if overwrite:
        deleteIfItExists(fire_intersect_file, True)
        deleteIfItExists(lightening_with_multiples, True)
        deleteIfItExists(lightening_temp, True)
    if not arcpy.Exists(fire_intersect_file):
        print "          - Creating interection layer for multiple fire areas"
        arcpy.Intersect_analysis(fire_temp_file, fire_intersect_file, "ALL", "", "INPUT")    # Process: Intersect creates a layer with just the fires that overlap
    if not arcpy.Exists(lightening_temp):
        if not arcpy.Exists(lightening_with_multiples):
            print "          - Joining Interesection layer to lightening strikes"
            arcpy.SpatialJoin_analysis(lightening_aoi_path, fire_intersect_file, lightening_with_multiples)  # Process: Spatial Join adds the date for ovelapping fires into a new table as "DiscDate"
        print "          - Joining individual fires layer to lightening strikes"
        arcpy.SpatialJoin_analysis(lightening_with_multiples, fire_temp_file, lightening_temp)      # Process: Spatial Join  adds the date for all fires into a new table as "DiscDate_1"
        print "          - creating coded field"
        codeblock = "def existance(both,date_single):\\n    if both is not None:\\n        return 2\\n    elif date_single is not None:\\n        return 1\\n    else:\\n        return 0"
        arcpy.AddField_management(lightening_temp, overlap_field, "SHORT", "", "", "","", "NULLABLE")
        arcpy.CalculateField_management(lightening_temp, overlap_field, "existance( !DiscDate!, !DiscDate_1! )", "PYTHON_9.3", codeblock)    # Process: Calculate Field creates the overlap field with 0 for no overlap, 1 for a sinlge and 2 for both
        print "          - renaming fields"
        arcpy.AddField_management(lightening_temp, single_date_field, "DATE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "") # Process: Add Field creates a field for the date of single overlap fires
        arcpy.CalculateField_management(lightening_temp, single_date_field, "[DiscDate_1]", "VB", "")


        fields_orig = arcpy.ListFields(lightening_path) #Generating a list to delete all the extra fields
        fields_new = arcpy.ListFields(lightening_temp)
        drop_fields2 = []
        fn_orig = [overlap_field,single_date_field]
        for f2 in fields_orig:
            fn_orig.append(str(f2.name))
        for f1 in fields_new:
            if not f1.name in fn_orig:
                drop_fields2.append(str(f1.name))


        arcpy.DeleteField_management(lightening_temp, drop_fields2) #Should be a way to do this automatically
        print "          - cleaning up temporary files"
        arcpy.CopyFeatures_management(lightening_temp, lightening_with_all)
        deleteIfItExists(lightening_with_multiples,True)
        deleteIfItExists(fire_temp_file, True)
        deleteIfItExists(lightening_temp, True)
        deleteIfItExists(fire_intersect_file, True)

#roeii

def existance(both,date_single):
    """
    This is a selection for a particular field. Used in arcGIS with the Python Interpretator. Exactly the same as the variable codeblock
    """
    if both is not None:
        return 2
    elif date_single is not None:
        return 1
    else:
        return 0
def returnArea(the_file):
    """
    Given a file with one feature, this calculates and extracts the area of that feature
    """
    arcpy.AddGeometryAttributes_management(the_file, "AREA", "", "SQUARE_KILOMETERS","")
    arcpy.MakeFeatureLayer_management(the_file, "temp_lyr")
    total_num = int(str(arcpy.GetCount_management("temp_lyr")))
    if total_num  == 1:
        temp_cursor = arcpy.SearchCursor("temp_lyr")

        for each_feature in temp_cursor:
            value =  float(str(each_feature.getValue("POLY_AREA")))
        del temp_cursor
        deleteIfItExists("temp_lyr", True)
        return value
    else:
        print "ERROR"
        deleteIfItExists("temp_lyr", True)
        return 0

def processing():
    """
    Main processing of files.  Should take about 1-2 hours to run since it no longer does calculations for anything but strikes that overlap multiple fire
    11-21-2014: changed the logic so that before and after are variables that work on strikes from the same year
    """
    print "2). Processing"
    each_fire_year_lyr = "each_fire_year_layer"
    each_lightening_year_lyr = "each_lightening_year_layer"
    each_iterated_fire_layer = "each_iterated_fire_layer"
    each_iterated_lightening_layer = "each_iterated_lightening_layer"
    print
    for each_year in all_years:
        print "   ",  each_year,
        lightening_year_selc = "EXTRACT( YEAR FROM \"{0}\")  = {1}".format(lightening_date_field, each_year)
        fire_year_selc = "EXTRACT( YEAR FROM \"{0}\")  <= {1} AND EXTRACT( YEAR FROM \"{0}\")  >= {2}".format(fire_date_field, each_year + 1, each_year - YEAR_GAP)

        deleteIfItExists(each_lightening_year_lyr, True)
        deleteIfItExists(each_fire_year_lyr, True)
        arcpy.MakeFeatureLayer_management(lightening_with_all_lyr, each_lightening_year_lyr, lightening_year_selc)
        arcpy.MakeFeatureLayer_management(fire_areas_aoi_lyr, each_fire_year_lyr, fire_year_selc)
        total_num = int(str(arcpy.GetCount_management(each_lightening_year_lyr)))
        print "total = ",total_num,


        temp_fire_lyr = "temp_fire_lyr"
        each_strike_lyr = "each_strike_layer"
        deleteIfItExists(each_iterated_fire_layer, True)
        deleteIfItExists(each_iterated_lightening_layer, True)
        arcpy.MakeFeatureLayer_management(each_fire_year_lyr, each_iterated_fire_layer)
        arcpy.MakeFeatureLayer_management(each_lightening_year_lyr, each_iterated_lightening_layer)
        strike_cursor = arcpy.SearchCursor(each_iterated_lightening_layer)
        old = 0
        new = 0
        outside = 0
        overlap = 0
        before = 0
        after = 0
        #for each_strike in strike_cursor:
        #each_strike = strike_cursor.next()
        counter =0
        each10 = total_num // 10
        count10 = each10
        for each_strike in strike_cursor:
            if counter == count10: # This is here to mark progress through a file
                print ".",
                count10 +=each10
            overlap_value = int(str(each_strike.getValue(overlap_field)))
            if overlap_value == 0 : #Checking for strikes that do not overlap anything
                outside +=1
            elif overlap_value == 1:    #Checking for any strikes that overlap a single fire
                strike_date = each_strike.getValue(lightening_date_field) #pulls the strike date
                single_fire_date = each_strike.getValue(single_date_field) #pulls the fire date
                days_difference = abs(single_fire_date - strike_date).days # calculatesnumber of days between the two
                if days_difference <= DAY_RANGE:    #checking if that strike happens withing the day range
                    new +=1
                    #if it falls within the range, it is counted as a new strike
                else: #if it is not within the range
                    if single_fire_date < strike_date:  #if not, is it before the fire?
                        #if it is befre the fire , is it within the year range (here it is 10 years)
                        if ((strike_date - single_fire_date).days / 365.2425) < YEAR_GAP:
                            old += 1
                        # Otherwise, it gets the value of outside
                        else:
                            outside +=1
                    else:   #if nothing else, it is after the fire
                        before +=1
                        #print "b1",
            else:   #finally, checking those strikes that overlap more than one fire polygon
                strike_date = each_strike.getValue(lightening_date_field)
                eachID = each_strike.getValue(lightening_index_field)
                selc = "\"%s\" = %s " %(lightening_index_field, eachID)
                deleteIfItExists(each_strike_lyr, True)
                arcpy.MakeFeatureLayer_management(each_iterated_lightening_layer, each_strike_lyr, selc)
                arcpy.SelectLayerByLocation_management(each_iterated_fire_layer, "INTERSECT", each_strike_lyr, "", "NEW_SELECTION") #Creates a layer from
                num_overlaps = int(str(arcpy.GetCount_management(each_iterated_fire_layer)))
                if num_overlaps == 0:
                    outside +=1
                    #print "out3",
                elif num_overlaps == 1:
                    single_fire_date = each_strike.getValue(single_date_field)
                    days_difference = abs(single_fire_date - strike_date).days
                    if days_difference <= DAY_RANGE:
                        new +=1
                        #print "n2",
                    else:
                        if single_fire_date < strike_date:
                            old += 1
                            #print "old2",
                        else:
                            before +=1
                            #print "b2",
                else:
                    new_in_sample = False
                    old_in_sample = False
                    fire_cursor = arcpy.SearchCursor(each_iterated_fire_layer)
                    for each_fire in fire_cursor:
                        fire_date = each_fire.getValue(fire_date_field)
                        days_difference = abs(fire_date - strike_date).days
                        if days_difference <= DAY_RANGE:
                            new_in_sample = True
                        else:
                            if fire_date < strike_date:
                                old_in_sample = True
                    if new_in_sample:
                        new +=1
                        #print "n3",
                    else:
                        old +=1
                        #print "old3",
                    if new_in_sample and old_in_sample:
                        overlap +=1
                        #print "OVERLAP", eachID
            counter +=1
            if counter == break_counter: #This is just to break the loop at a specific level, keeps it from running all 280 cells
                print
                print "Reached Max Iterations"
                break
            del each_strike
            deleteIfItExists(strike_cursor, True)

        print
        print "          old = {0}, new = {1}, outside = {2}, overlap = {3}, before = {4}, total = {5}".format(old,new,outside,overlap,before, total_num)
        new_line = "{0},{1},{2},{3},{4},{5},{6},{7}".format(each_year,total_num,old,new,outside,before,after,overlap)
        logFileWriter = open(strikes_output_file_path, 'a')
        logFileWriter.write(new_line + "\n")
        logFileWriter.close()

def calculateFireAreas():
    """
    For each year, calculates the area of fire scars for that year, the area of fire scars from the previous 10 years
    and the area not covered by a fire scar
    """

    total_area = returnArea(AOI_path)
    print "Total Area = {0} km2".format(total_area)
    current_year_lyr = "current_year_lyr"
    prev_years_lyr = "prev_years_lyr"
    all_years_lyr = "all_years_lyr"
    current_year_lyr_dis = "current_year_lyr_dis"
    prev_years_lyr_dis = "prev_years_lyr_dis"
    all_years_lyr_dis = "all_years_lyr_dis"
    intersect_lyr = "intersect_lyr"
    logFileWriter = open(fires_output_table, 'w')
    logFileWriter.write(fires_header + "\n")


    working_fire_clipped = output_directory + "Fire_clipped_temp.shp"
    if not arcpy.Exists(working_fire_clipped):
        arcpy.Clip_analysis(fire_area_aoi_path, AOI_path, working_fire_clipped, "")
    arcpy.AddGeometryAttributes_management(working_fire_clipped, "AREA","","SQUARE_KILOMETERS","")
    temp_each_year_file =  "E:\\GISWork_2\\Lightening\\Outputs\\each_year.shp"
    temp_prev_year_file =  "E:\\GISWork_2\\Lightening\\Outputs\\prev_year.shp"
    temp_all_year_file =  "E:\\GISWork_2\\Lightening\\Outputs\\all_year.shp"
    temp_intersect_file = "E:\\GISWork_2\\Lightening\\Outputs\\overlap.shp"
    temp_intersect_dis_file = "E:\\GISWork_2\\Lightening\\Outputs\\overlap_dis.shp"
#Real stuff
    for each_year in all_years:
        all_delete = [temp_intersect_dis_file, intersect_lyr, temp_intersect_file, temp_all_year_file,temp_each_year_file,temp_prev_year_file,current_year_lyr,prev_years_lyr,all_years_lyr]
        for oil in all_delete:
            deleteIfItExists(oil, True)

        fire_this_year_selc = "EXTRACT( YEAR FROM \"{0}\")  = {1}".format(fire_date_field, each_year)
        fire_prev_years_selc =  "EXTRACT( YEAR FROM \"{0}\")  < {1} AND EXTRACT( YEAR FROM \"{0}\")  >= {2}".format(fire_date_field, each_year, each_year - YEAR_GAP)
        fire_all_selc = "EXTRACT( YEAR FROM \"{0}\")  <= {1} AND EXTRACT( YEAR FROM \"{0}\")  >= {2}".format(fire_date_field, each_year, each_year - YEAR_GAP)
        arcpy.MakeFeatureLayer_management(fire_areas_aoi_lyr, current_year_lyr,fire_this_year_selc)
        arcpy.MakeFeatureLayer_management(fire_areas_aoi_lyr, prev_years_lyr,fire_prev_years_selc)
        arcpy.MakeFeatureLayer_management(fire_areas_aoi_lyr, all_years_lyr,fire_all_selc)
        num_current = int(str(arcpy.GetCount_management(current_year_lyr)))
        num_past = int(str(arcpy.GetCount_management(prev_years_lyr)))
        arcpy.Dissolve_management(current_year_lyr, temp_each_year_file, "", "","", "")
        arcpy.Dissolve_management(prev_years_lyr, temp_prev_year_file, "", "","", "")
        arcpy.Dissolve_management(all_years_lyr, temp_all_year_file, "", "","", "")
        arcpy.Intersect_analysis([current_year_lyr,prev_years_lyr],temp_intersect_file)
        arcpy.MakeFeatureLayer_management(temp_intersect_file, intersect_lyr)
        num_overlap = int(str(arcpy.GetCount_management(intersect_lyr)))
        arcpy.Dissolve_management(intersect_lyr, temp_intersect_dis_file, "", "","", "")

        overlap_area = returnArea(temp_intersect_dis_file)
        each_year_area = returnArea(temp_each_year_file)
        prev_year_area = returnArea(temp_prev_year_file)
        all_year_area =  returnArea(temp_all_year_file)

        each_line = "{0},{1},{2},{3},{4},{5},{6},{7}".format(each_year,num_current,each_year_area,num_past,prev_year_area, total_area - all_year_area, num_overlap, overlap_area)
        print each_line
        logFileWriter.write(each_line + "\n")
    logFileWriter.close()
def testingInstance():
    for each_year in all_years:
        fire_this_year_selc = "EXTRACT( YEAR FROM \"{0}\")  = {1}".format(fire_date_field, each_year)
        fire_prev_years_selc =  "EXTRACT( YEAR FROM \"{0}\")  < {1} AND EXTRACT( YEAR FROM \"{0}\")  >= {2}".format(fire_date_field, each_year, each_year - YEAR_GAP)
        fire_all_selc = "EXTRACT( YEAR FROM \"{0}\")  <= {1} AND EXTRACT( YEAR FROM \"{0}\")  >= {2}".format(fire_date_field, each_year, each_year - YEAR_GAP)
        print each_year
        print fire_this_year_selc
        print fire_prev_years_selc
        print fire_all_selc
#Main program
start = timeit.default_timer() #This is just to time how long the program run.  Can be safely Omitted



preProcessing()
#processing()
calculateFireAreas()
#testingInstance()


#Last bit just to create an time output
stop = timeit.default_timer()
seconds = stop - start
m, s = divmod(seconds, 60)
h, m = divmod(m, 60)
print
print "Total Runtime = %d:%02d:%02d" % (h, m, s)
#raw_input()
