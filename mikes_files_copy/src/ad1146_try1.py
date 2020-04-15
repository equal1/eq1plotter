
print 'This is a Python Pygram script for accessing Atlantis Database Sweep data' 

# Get the main pygram object so we can import data
# and add our own plots within this script
import __main__ as M
pygram = M.mag

# Remove all previous pygram log data
pygram.wclearfiles()


# Connect to the Atlantis database, and return a cursor
# so that we can write SQL commands
pygram.atlantis_set_dsn('Greensboro')
cnxn = pygram.connect(pygram.atlantis_dsn)
cursor = cnxn.cursor()


EventID = 2213962
PartNum = 'AD1146'

# Preload the main test data for the given EventID (the test ID number),
# but do not load the sweep data, as this will be done later.
pygram.atlantis_load_test( cursor, eventid=EventID, mode='no_sweepdata' ) 


print 'done load 1'

# SQL to return all the sweep data (ie the sparameter data)
sql = """
    SELECT DISTINCT  
       CondData.LoopNum, 
       SweepParams.TestName,  
       SweepData.ArrayPoint, 
       SweepData.XValue,  
       SweepData.YValue, 
       SweepData.ZValue, 
       SweepParams.XParam,  
       SweepParams.YParam, 
       SweepParams.ZParam
    FROM  TestEvents
       INNER JOIN SweepData ON SweepData.EventID=TestEvents.EventID 
       INNER JOIN CondData ON CondData.EventID=TestEvents.EventID and SweepData.LoopNum = CondData.LoopNum
       INNER JOIN SweepParams ON SweepParams.SweepID=SweepData.SweepID 
    WHERE TestEvents.EventID=%s and SweepParams.PartNum='%s' 
    ORDER BY CondData.LoopNum, SweepParams.TestName, SweepData.ArrayPoint
    """ % (EventID, PartNum)

cursor.execute(sql)
rows = cursor.fetchall() 


print 'length of rows =', len(rows)
print 'done load 2'

last_LoopNum = None
first_CondParam = None
valmaxlist = []
freqlist = []

# Go through all the records and find the max for each of the sweeps
for row in rows:            
        
    # Get the test type name
    TestName   = row[1]

    # Only look for the S21 test data    
    if TestName == 'S21 vs. Frequency':

        # Get the LoopNum, if it changed then reset all the sweep calculations
        LoopNum    = row[0]
        if LoopNum != last_LoopNum:
            valmax = None
            valmaxlist.append( None )
            freqlist.append( None )
        last_LoopNum = LoopNum

        # Get the XValue - This is the Frequency value
        freq = float(row[3])
    
        # Get the YValue - This is the dB value
        # If the data is in R I format then we would also need to get the ZValue
        # and convert YValue and the ZValue to a dB or Magnitude value 
        val  = float(row[4])

        # Find the max value and the frequency 
        if valmax==None or val > valmax:
            valmax = val
            valmaxlist[-1] = val
            freqlist[-1] = freq

print 'done load 3'

# Add the new data into the Pygram data structure
pygram.data[ 's21_max(dB)' ]  = valmaxlist    
pygram.data[ 's21_max(MHz)' ] = freqlist    

# Update the Pygram Gui with the new test columns
pygram.win_load()

# Close the database connection, 
# (not sure, could we close the connection immediately after executing the sql?)
cnxn.close()




