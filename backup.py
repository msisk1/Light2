for each_strike in strike_cursor:
            if counter == count10: # This is here to mark progress through a file
                print ".",
                count10 +=each10
            overlap_value = int(str(each_strike.getValue(overlap_field)))
            if overlap_value == 0 : #Checking for strikes that do not overlap anything
                struck_outside +=1
            elif overlap_value == 1:    #Checking for any strikes that overlap a single fire
                strike_date = each_strike.getValue(lightening_date_field) #pulls the strike date
                single_fire_date = each_strike.getValue(single_date_field) #pulls the fire date
                days_difference = abs(single_fire_date - strike_date).days # calculates number of days between the two
                if days_difference <= DAY_RANGE:    #checking if that strike happens within the day range
                    struck_new_scar +=1
                    #if it falls within the range, it is counted as a new strike
                else: #if it is not within the range
                    if single_fire_date < strike_date:  #if not, is it before the fire?
                        if single_fire_date.year == strike_date.year: # Did it strike within the same year? 
                            struck_same_year_after_fire += 1 
                        #if it struck after the fire , is it within the year range (here it is 10 years)
                        #elif ((strike_date - single_fire_date).days / 365.2425) < YEAR_GAP: #LIKE THIS IT DOES NOT DUPLICATE STRIKES AFTER THE FIRE INTO SAME_YEAR_BEFORE AND STRUCK_OLD
                        elif ((strike_date.year - single_fire_date.year)) < YEAR_GAP: #LIKE THIS IT DOES NOT DUPLICATE STRIKES AFTER THE FIRE INTO SAME_YEAR_BEFORE AND STRUCK_OLD 
                            struck_old_scar += 1
                        else: # Otherwise, it gets the value of outside because the fire is more than 10 years before
                            struck_outside +=1
                    else:   #if nothing else, it must be a strike after the fire
                        if single_fire_date.year == strike_date.year: 
                            struck_same_year_b4_fire +=1 #if it is the same year than struck same year after fire
                        else: # if not, than struck outside
                            struck_outside+=1
            else:   #finally, checking those strikes that overlap more than one fire polygon
                strike_date = each_strike.getValue(lightening_date_field)
                eachID = each_strike.getValue(lightening_index_field)
                selc = "\"%s\" = %s " %(lightening_index_field, eachID)
                deleteIfItExists(each_strike_lyr, True)
                
                arcpy.MakeFeatureLayer_management(each_iterated_lightening_layer, each_strike_lyr, selc) #Creates a new feature layer from the strike
                arcpy.SelectLayerByLocation_management(each_iterated_fire_layer, "INTERSECT", each_strike_lyr, "", "NEW_SELECTION") #Creates a layer composed of those scars that overlap the feature
                #Note: Becasue the fire layer is already selected by the data range from the strike, even though the value for overlap_value might be more than 1, there may be 0 actual overlaps
                num_overlaps = int(str(arcpy.GetCount_management(each_iterated_fire_layer)))
                if num_overlaps == 0:
                    struck_outside +=1
                elif num_overlaps == 1: #Thus is this duplicated from above at "elif overlap_value ==1"
                    strike_date = each_strike.getValue(lightening_date_field) #pulls the strike date
                    single_fire_date = each_strike.getValue(single_date_field) #pulls the fire date
                    days_difference = abs(single_fire_date - strike_date).days # calculates number of days between the two
                    if days_difference <= DAY_RANGE:    #checking if that strike happens within the day range
                        struck_new_scar +=1
                        #if it falls within the range, it is counted as a new strike
                    else: #if it is not within the range
                        if single_fire_date < strike_date:  #if not, is it before the fire?
                            if single_fire_date.year == strike_date.year: # Did it strike within the same year? 
                                struck_same_year_after_fire += 1 
                            #if it struck after the fire , is it within the year range (here it is 10 years)
                            
                            #elif ((strike_date - single_fire_date).days / 365.2425) < YEAR_GAP: #LIKE THIS IT DOES NOT DUPLICATE STRIKES AFTER THE FIRE INTO SAME_YEAR_BEFORE AND STRUCK_OLD
                            elif ((strike_date.year - single_fire_date.year)) < YEAR_GAP:
                                struck_old_scar += 1
                            else: # Otherwise, it gets the value of outside because the fire is more than 10 years before
                                struck_outside +=1
                        else:   #if nothing else, it must be a strike after the fire
                            if single_fire_date.year == strike_date.year: 
                                struck_same_year_b4_fire +=1 #if it is the same year than struck same year after fire
                            else: # if not, than struck outside
                                struck_outside+=1
                else: #This one means there are definitely multiple features
                    new_in_sample = False
                    old_in_sample = False
                    same_year_before = False
                    same_year_after = False
                    fire_cursor = arcpy.SearchCursor(each_iterated_fire_layer)
                    for each_fire in fire_cursor:
                        fire_date = each_fire.getValue(fire_date_field)
                        days_difference = abs(fire_date - strike_date).days
                        if days_difference <= DAY_RANGE:
                            new_in_sample = True
                        else:
                            if single_fire_date.year == strike_date.year: 
                                if single_fire_date < strike_date:
                                    same_year_after = True 
                                if single_fire_date > strike_date:
                                    same_year_before = True
                            if fire_date < strike_date: ##It is already the correct year range, so no worries here about checking for years
                                old_in_sample = True
                    if new_in_sample: #then it hit a new and that is all we care about
                        struck_new_scar +=1
                    else: #then it hit at least one old one, but regardless, it should be added only once
                        if same_year_after:
                            struck_same_year_after_fire+=1
                        elif same_year_before :
                            struck_same_year_b4_fire +=1
                        else:
                            struck_old_scar +=1
                    if new_in_sample and old_in_sample:
                        struck_overlap +=1