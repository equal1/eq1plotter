/* ========================================================================== */
/*                                                                            */
/*   Filename.c                                                               */
/*   (c) 2001 Author                                                          */
/*                                                                            */
/*   Description                                                              */
/*                                                                            */
/* ========================================================================== */

#include <stdio.h>
#include <ctype.h>
#include <string.h>
#include <stdlib.h>


#define  GSM850						     0
#define  GSM                             1
#define  EGSM                        	 2
#define  DCS                             3
#define  PCS                             4
#define  INVALID_RANGE_BAND              9

#define START_FREQ						 0
#define STOP_FREQ						 1
#define RBW								 2
#define VBW								 3
#define ABS_START_LMT					 4

#define SPUR_RANGE_TABLE_SIZE            14

#define SPUR_RANGE_FILE                  "spur_range_def_quick.lis"
#define A_4440A                          4440

#define MAXLINE                          256


int smcbaspanel = 0;
int SMCBasPnl_OperatorInfo = 0;
void InsertTextBoxLine (int smcbaspanel, int SMCBasPnl_OperatorInfo, int stat,  char *errstr);


float  GRangeTable[14][5][5];
float  GRangeTableIsRelFreq[14][5][2];
int    GRangeTableNum;
char   g_values[20][MAXLINE];

/*
int    SetupRangeTableFromFile();
void   UpdateRangeTableFromFreq( float , int , char * );
void   BuildRangeTableCmd( char *, char *, int, int );
int    GetLineVals( FILE *fp, int * );
*/

void BuildRangeTableCmd( char *str, char *prefix, int bandIndex, int idx );
void UpdateRangeTableFromFreq( float freqVal, int bandIndex, char *range_enable_state );
int  GetLineVals( FILE *fp, int *linenum, int *status );
int  SetupRangeTableFromFile();

// BuildRangeCmd     ver 301ma
// For use with Spur Range Tables loaded form SPUR_RANGE_FILE
// This function creates a SCPI string by reading values from the
// GRangeTable array.
// It uses the prefix parameter as the start of the SCPI command and
// postfixes it with the values from the GRangeTable array for the all the ranges
// and for the bandIndex specified
void BuildRangeTableCmd( char *str, char *prefix, int bandIndex, int idx )
{
    int i;
    char valstr[MAXLINE] ;
    char delim[10];

    strcpy( str, prefix );

    for (i=0; i<SPUR_RANGE_TABLE_SIZE; i++)
    {
       if (i==0) strcpy(delim,"" );
       else      strcpy(delim,",");
       sprintf( valstr, "%s%f", delim, GRangeTable[i][bandIndex][idx] );
       strcat( str, valstr );
    }

}







// UpdateRangeTableFromFreq
// Frequency values in the GRangeTable may be relative to the Test Frequency
// if so the GRangeTable frequency values need to be recalculated based on the
// Test frequency (freqVal)

void UpdateRangeTableFromFreq( float freqVal, int bandIndex, char *range_enable_state )
{
      int i, j, do_range;

      for (i=0; i<SPUR_RANGE_TABLE_SIZE; i++)
      {
          for (j=0; j<5; j++)
          {
             if ( GRangeTableIsRelFreq[i][j][START_FREQ] != 0 )
                 GRangeTable[i][j][START_FREQ]    =   (freqVal * 1e6 ) + GRangeTableIsRelFreq[i][j][START_FREQ];
             if (GRangeTableIsRelFreq[i][j][STOP_FREQ] != 0 )
                 GRangeTable[i][j][STOP_FREQ]     =   (freqVal * 1e6 ) + GRangeTableIsRelFreq[i][j][STOP_FREQ];
          }
      }


	  strcpy( range_enable_state, "" );
	  for (i=0; i<SPUR_RANGE_TABLE_SIZE; i++)
      {

          if ( GRangeTable[i][bandIndex][START_FREQ] != 0 ) do_range = 1;
          else                                              do_range = 0;


          if (i==0)           {  strcat( range_enable_state, " "  ); }
          else                {  strcat( range_enable_state, "," ); }

          if (do_range == 1 ) {  strcat( range_enable_state, "ON"  ); }
          else                {  strcat( range_enable_state, "OFF" ); }
      }

}




// GetLineVals
// Function to read a line of comma separated data values from the SPUR_RANGE_FILE
// It ignores any comments, and does limited checking on the values
// and prints out error message if any of the values on the line are not legal.
// It writes the results into a global a list of values (values[]) and returns
// the number of values found (NumVals)
// If the end of the file is reached it returns 0 (NULL)

int GetLineVals( FILE *fp, int *linenum, int *status )
{
      char  *p1, *p2, *p3, *tok, *searchstr;
      char  line[MAXLINE], buf[MAXLINE], errstr[MAXLINE];
      int   NumVals = 0;

      char  searchstr1[] = "0123456789.+-";
      char  searchstr2[] = "0123456789.+-Fc";

      while( fgets(line,MAXLINE,fp) )
      {
          (*linenum)++;

          p2 = buf;

          // copy the valid characters from 'line' into 'buf' ignoring spaces and comments
          for(p1=line; *p1!='\0'; p1++)
          {
               if (*p1=='#') { break; }  // truncate the line at the first comment char
               if ( ! isspace( *p1 ) )
               {
                   *p2 = *p1;
                   p2++;
               }
          }
          if ( p2 > buf )
          {
//             *p2++ = '\n';
             *p2++ = '\0';

             NumVals = 0;
             sprintf( g_values[NumVals++], "%d", *linenum );

             tok = strtok( buf, ",");
             while(tok != NULL)
             {
                 strcpy( g_values[NumVals] , tok );

                 // Check for legal values  on the line. Values should contain valid number digits, plus the [Fc] characters for start and stop freq values
                 // Any characters are allowed for the subband value (the subband will be checked later)
                 if( NumVals < 7 ) {
                    if (NumVals == 2 || NumVals == 3 )  { searchstr = searchstr2; }
                    else                                { searchstr = searchstr1; }
                    for ( p3 = tok; *p3 != '\0'; p3++ )  {

                        if ( !strchr( searchstr, *p3 )) {
                            *status = 1;
                            sprintf( errstr, "*** ERROR *** %s (Line %d) Value %d (%s) uses illegal characters. Only these characters are allowed for this value '%s'", SPUR_RANGE_FILE, *linenum, NumVals, tok, searchstr );
                        	InsertTextBoxLine (smcbaspanel, SMCBasPnl_OperatorInfo, -1,  errstr);
                            break;
                        }

                    }
                 }

                 tok = strtok(NULL, ",");
                 NumVals++;
             }
             return NumVals;

          }

      }
      return NumVals;
}



//   SetupRangeTableFromFile
//  Function that reads the SPUR_RANGE_FILE and updates the GRangeTable and GRangeTableIsRelFreq arrays
//  These arrays are used to define the PSA ranges during a Spurious Emmision Test.
//  Currently this function is used only when running the Spur (Quick) test
//  It also writes the range_enable_state string which is string containing the ON/OFF state for each range
//  The range_enable_state string can be concatenated to the end of SCPI commands to form the full control string
int   SetupRangeTableFromFile()
{
      FILE *fp;
      int i, j, NumVals, range, subband, do_range;
      double  rbw, vbw, limit, startfreq, stopfreq, relative_start_freq, relative_stop_freq;
      char *sb, *p;
      int linenum  = 0;
      int status;
      char errstr[MAXLINE];


      // reset the whole GRangeTable
      for (i=0; i<SPUR_RANGE_TABLE_SIZE; i++)
      {
          for (j=0; j<5; j++)
          {
             GRangeTable[i][j][START_FREQ]    = 0;
             GRangeTable[i][j][STOP_FREQ]     = 0;
             GRangeTable[i][j][RBW]           = 0;
             GRangeTable[i][j][VBW]           = 0;
             GRangeTable[i][j][ABS_START_LMT] = 0;
             GRangeTableIsRelFreq[i][j][START_FREQ] = 0;
             GRangeTableIsRelFreq[i][j][STOP_FREQ]  = 0;
          }
      }


      if ((fp = fopen( SPUR_RANGE_FILE, "r")) == NULL)
      {
          sprintf( errstr, "*** ERROR *** (SetupRangeTableFromFile) Cannot read  SPUR_RANGE_FILE file '%s'", SPUR_RANGE_FILE );
          InsertTextBoxLine (smcbaspanel, SMCBasPnl_OperatorInfo, -1,  errstr);
          return 1;
      }




      while ( NumVals = GetLineVals( fp, &linenum, &status ) )
      {

         range =  atoi( g_values[1] ) ;
         subband = -1;
         startfreq = atof( g_values[2] ) * 1e6;
         stopfreq  = atof( g_values[3] ) * 1e6;
         rbw       = atof( g_values[4] ) * 1e6;
         vbw       = atof( g_values[5] ) * 1e6;
         limit     = atof( g_values[6] ) ;

         // Look for a relative freq in the start and stop freq columns
         // If found we will set the relative_start_freq and relative_stop_freq flags
         // and write the freq to the GRangeTableIsRelFreq array

         p =   g_values[2];
         if ( strstr( p, "Fc" ) == p ) {
              p = p + 2;
              relative_start_freq = 1;
         } else {
              relative_start_freq = 0;
         }

         startfreq = atof( p ) * 1e6;

         p =   g_values[3];
         if ( strstr( p, "Fc" ) == p ) {
              p = p + 2;
              relative_stop_freq = 1;
         } else {
              relative_stop_freq = 0;
         }

         stopfreq = atof( p ) * 1e6;




         if ( range < 1 || range > 14 ) {
            status = 1;
            sprintf( errstr, "*** ERROR *** %s (Line %s) Range is '%d', it must be Range >= 1 or Range <= 14", SPUR_RANGE_FILE, g_values[0], range );
           	InsertTextBoxLine (smcbaspanel, SMCBasPnl_OperatorInfo, -1,  errstr);
            range = 1;
         }
         if ( ! ( NumVals == 7 || NumVals == 8 )) {
            status = 1;
            sprintf( errstr, "*** ERROR *** %s (Line %s) Wrong number of parameters (=%d), there should be 6 or 7 comma seperated values on the line", SPUR_RANGE_FILE, g_values[0], NumVals-1 );
           	InsertTextBoxLine (smcbaspanel, SMCBasPnl_OperatorInfo, -1,  errstr);
         }

         // find the subband for the range

         if ( NumVals == 8 ) {

            sb = g_values[7];
            if      (!strncmp(  sb, "GSM", 3  )) { subband = GSM850; }
            else if (!strncmp(  sb, "EGSM", 3 )) { subband = EGSM;   }
            else if (!strncmp(  sb, "DCS",  3 )) { subband = DCS;    }
            else if (!strncmp(  sb, "PCS",  3 )) { subband = PCS;    }
            else {
                status = 1;
                sprintf(errstr, "*** ERROR *** %s (Line %s) Illegal Sub-Band specified '%s' (Should be one of GSM850 EGSM900 DCS1800 PCS1900", SPUR_RANGE_FILE, g_values[0], sb );
               	InsertTextBoxLine (smcbaspanel, SMCBasPnl_OperatorInfo, -1,  errstr);
            }
         }

//         printf( "  rbw = '%s' -> %f\n", values[4], rbw );
//         printf( "  subband = '%s' -> %d\n", values[7], subband );
         range--;

         // Transfer the values for this range and subband into the GRangeTable array
         for( i=GSM850; i<=PCS; i++ ) {                  // Go through all the subbands from GSM850 to PCS
                  if( i==GSM ) { continue; }              // Ignore the GSM value, it is the same  GSM850
                  if( subband < 0 || subband == i ) {     // if the subband is set to -1 then write values to all 4 subbands, eles write only to the selected subband
                      GRangeTable[range][i][START_FREQ]    = (float) startfreq;
                      GRangeTable[range][i][STOP_FREQ]     = (float) stopfreq;
                      GRangeTable[range][i][RBW]           = (float) rbw;
                      GRangeTable[range][i][VBW]           = (float) vbw;
                      GRangeTable[range][i][ABS_START_LMT] = (float) limit;

                      // A Relative frequency was specified, then write the frequency to the  GRangeTableIsRelFreq array
                      // this will cause the real start and stop frequencies to be calculated when the test is running
                      if( relative_start_freq  == 1 ) {
                          GRangeTableIsRelFreq[range][i][START_FREQ]    = (float) startfreq;  }
                      if( relative_stop_freq   == 1 ) {
                          GRangeTableIsRelFreq[range][i][STOP_FREQ]     = (float) stopfreq;   }
                  }
         }


      }

      fclose(fp);

      return status;
}



void InsertTextBoxLine (int smcbaspanel, int SMCBasPnl_OperatorInfo, int stat,  char *errstr)
{
    printf( "%s\n", errstr );
}


void ibwrt (int instrument, char *cmdstr, int cmdlen)
{
   printf( "SCPI %10d, '%s' len=%d\n", instrument, cmdstr, cmdlen);
}



int main(void)
{
     int i,j,k ;
     char range_enable_str[ MAXLINE ] = "" ;
     char cmdstr[ MAXLINE ];
     int status;
     int bandIndex;

     status = SetupRangeTableFromFile();

     printf ("STATUS = %d\n", status );

/* Read the file */
/* and define the spur table   */

      bandIndex = PCS;

      UpdateRangeTableFromFreq(  1234, bandIndex, range_enable_str );

      // reset the whole GRangeTable

      for (i=0; i<SPUR_RANGE_TABLE_SIZE; i++)
      {
          printf("====  RANGE=%2d ===============================\n", i );
          for (j=0; j<5; j++)
          {
             printf( "Subband=%2d   ", j );

             for ( k=0; k<5; k++ ) {
                printf( "    %12.0f", GRangeTable[i][j][k] );
             }
             printf( "    %12.0f", GRangeTableIsRelFreq[i][j][0] );
             printf( "    %12.0f", GRangeTableIsRelFreq[i][j][1] );
             printf( "\n" );
          }

      }


      sprintf( cmdstr, "SPUR:STAT %s",   range_enable_str );
      ibwrt (A_4440A, cmdstr, strlen(cmdstr));

      BuildRangeTableCmd( cmdstr, "SPUR:FREQ:STAR ", bandIndex, START_FREQ);
      ibwrt (A_4440A, cmdstr, strlen(cmdstr));

      BuildRangeTableCmd( cmdstr, "SPUR:FREQ:STOP ", bandIndex, STOP_FREQ);
      ibwrt (A_4440A, cmdstr, strlen(cmdstr));

      BuildRangeTableCmd( cmdstr, "SPUR:BAND ", bandIndex, RBW);
      ibwrt (A_4440A, cmdstr, strlen(cmdstr));

      BuildRangeTableCmd( cmdstr, "SPUR:BWID:VID ", bandIndex, VBW);
      ibwrt (A_4440A, cmdstr, strlen(cmdstr));

      sprintf( cmdstr, "SPUR:SWE:TIME:AUTO %s",   range_enable_str );
      ibwrt (A_4440A, cmdstr, strlen(cmdstr));

      BuildRangeTableCmd( cmdstr, "CALC:SPUR:LIM:ABS:DATA:STAR ", bandIndex, ABS_START_LMT);
      ibwrt (A_4440A, cmdstr, strlen(cmdstr));


return 0;
}
