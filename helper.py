import re
try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk

import pymysql
import pandas
import numpy as np

def test_connection(host, user, password):
    try:
        pymysql.connect(host=host, user=user, password=password)
        connected = True
    except pymysql.err.OperationalError:
        connected = False
    return connected

def getDatabaseList(host='localhost',user='root', password=None):
    connection = pymysql.connect(host=host,user=user, password=password)
    cursor = connection.cursor()
    sql = "show databases"
    cursor.execute(sql)
    result = cursor.fetchall()
    return list(  map( lambda x : x[0], result ) ) 

def getTables( db_name, host='localhost', user='root', password=None):
    connection = pymysql.connect(host=host,user=user, password=password)
    cursor = connection.cursor()
    cursor.execute( 'use %s'%db_name )
    cursor.execute('show tables')
    result = cursor.fetchall()
    return list(  map( lambda x : x[0], result ) )

def mysql_to_dataframe( db_name , table_name, host='localhost', user='root', password=None):
    connection = pymysql.connect(host=host,user=user, password=password, db=db_name)
    cursor = connection.cursor()
    
    # Read a single record
    sql = "DESCRIBE %s"%table_name
    cursor.execute(sql)
    result_cols = cursor.fetchall()
    
    col_names = list(map(list, zip(*result_cols))) [0]
    col_types = list(map(list, zip(*result_cols))) [1]

    col_names = [ c for c,t in zip( col_names, col_types) if 'blob' not in t ]
    col_types = [ t for t in col_types if 'blob' not in t]

    sql = "SELECT %s from %s"%( ','.join(col_names) ,table_name)
    cursor.execute(sql)
    col_data = list(map(list,cursor.fetchall()))
            
    connection.close()

    # convert to python types
    datatypes = dict(  [ (col,str)   if t.startswith('varchar')
                       else (col,int )          if t.startswith('int')
                       else (col,float)        if t.startswith( 'double')
                       else (col,float )        if t.startswith( 'float')
                       else (col,'datetime64[ns]') if t.startswith('date')
                       else (col,None)
                       for col,t in zip(col_names, col_types)  ] ) 

    dataframe  = pandas.DataFrame( data = col_data , columns = col_names)
   
    for col,t in datatypes.iteritems():
        to_convert = dataframe[col].notnull()
        if t == str:
            dataframe.ix[ to_convert, col] = dataframe.ix[to_convert,col ].map( lambda x: x.decode( encoding='ascii', errors='ignore'))
        elif not t:
            dataframe.ix[ to_convert, col] = dataframe.ix[to_convert,col ].map( lambda x: x.decode( encoding='ascii', errors='ignore'))

    return datatypes, dataframe 

def addStemsFromTable(df, db_name , table_name,  multi_stem_col_expression, 
                        host='localhost', user='root', password=None):
#   connect to the eql database
    connection = pymysql.connect(host=host,user=user, password=password, db=db_name)
    cursor     = connection.cursor()

#   get the mysql table    
    sql        = "DESCRIBE %s"%table_name
    cursor.execute(sql)

#   get the column names
    col_names = [r[0] for r in cursor.fetchall()]

#   get the data and transpose it
    sql       = "SELECT * from %s"%table_name
    cursor.execute(sql)
    col_data  = list(map(list, zip(*cursor.fetchall()))) # transpose

#   make a dataframe 
    mstems_df = pandas.DataFrame.from_dict( {n: col_data[i] for i,n in enumerate(col_names) } )
    mstems_df.rename( columns=lambda x:x.lower(), inplace=True)
    
    mstems_col_names = filter( lambda x:re.match(multi_stem_col_expression,x), list(mstems_df))
    mstems_df = mstems_df[ ['tag']+mstems_col_names ] 
#   max nomstem from main database
    max_nomstem = len( filter( lambda x:re.match('dbh_',x), list(df) )  )
#   rename the columns to a standard name
    mstems_df.rename( columns={ name:'dbh_%d'%(i+max_nomstem+1) for i,name in enumerate(mstems_col_names) }, inplace=True )

    return pandas.merge( df,mstems_df, on='tag', how='outer')

def addStemsFromNotes(df):
#   find multi stem data in the notes columns
    df.loc[ df.notes.isnull(), 'notes']  = ''
    mstem_from_notes = df.notes.map( lambda x: re.findall('[0-9]{1,2}\.[0-9]*' , x) ) 

#   make all notes lower case for easier logical comparison
    df.notes       = df.notes.map( lambda x:x.lower() )

#   filter out mstam matches from notes, where mstem is actually a single dbh measurement of the main stem
    not_mstem_condition = [ 'stem' not in note 
                            and 'previous' in note 
                            and len(matches)==1 
                            and 'maybe' in note 
                            or 'past' in note 
                            for note,matches in zip(df.notes, mstem_from_notes) ]
    mstem_from_notes[ not_mstem_condition ] = None

#   max nomstem from main database
    max_nomstem = len( filter( lambda x:re.match('dbh_',x), list(df) )  )

#   create a mapping from mstem_from_notes series to a new dataframe, where the columns are the mstem dbh measurements
    mstems_map = [ {'dbh_%d'%(i+max_nomstem+1):float(val) for i,val in enumerate(vals) }  if vals else {} for vals in mstem_from_notes.values ]
    mstems_df = pandas.DataFrame( mstems_map, index=mstem_from_notes.index )

    return pandas.concat( (df, mstems_df) ,axis=1 )


def get_ctfs_col_info():
    data = {'dbh': 'Diameter of the stem.', 
        'substrate': 'Describes the ground surface where tree is planted', 
        'pom': 'The point-of-measure, where the diameter was taken, identical \n\
                to hom, but a character variable with only 2 decimal places.', 
        'ExactDate': 'The date on which the stem was measured.', 
        'notes': 'A column of field notes.', 
        'sp': 'The species mnemonic. This mnemonic is crucial in joining various\n\
                databases.', 
        'slp': 'standng, leaning, or prone (S,L, or P)',
        'pig_damage': 'column describing the pig damage (Typically 0,1,2, or 3 \n\
                    depending on the level of damage, 3 being worst)',
        'RawStatus': 'status of the tree, alive, dead, new, etc',
        'nostems': 'The number of living stems on the date of measurement.', 
        'tag': 'Tag number used in the field.', 
        'x': 'The x coordinate within the plot.', 
        'y': 'The y coordinate within the plot.', 
        'quadrat': 'Quadrat designation', 
        'subquad': 'Subquad within the quadrat (if applicable)', 
        'dist_to_nail': 'Distance from the nail to the measuring point as efined\n\
                    in the HIPPNET manual.'}

    return np.array( data.items() )


class ScrollList(tk.Frame):
    def __init__(self, master, *args, **kwargs):
        tk.Frame.__init__(self,master,*args, **kwargs)
#       make the widgets
        self.canv = tk.Canvas(self)
        self.X_scroll = tk.Scrollbar(self.canv, orient='horizontal')
        self.Y_scroll = tk.Scrollbar(self.canv, orient='vertical')
        self.lsbx = tk.Listbox(self.canv,exportselection=False,
                              xscrollcommand=self.X_scroll.set,
                              yscrollcommand=self.Y_scroll.set)

        self._config()
        self._pack_widgets()

    def _config(self):
        self.X_scroll.config(command=self.lsbx.xview)
        self.Y_scroll.config(command=self.lsbx.yview)

    def _pack_widgets(self):
        self.canv.pack(fill=tk.BOTH, expand=tk.YES)
        self.X_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.Y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.lsbx.pack(fill=tk.BOTH,expand=True)

    def fill(self,lines):
        """fill the listbox"""
        self.lsbx.delete(0, tk.END)
        lines = list(lines)
        if lines:
            for line in lines:
                self.lsbx.insert(tk.END,line)
            self.lsbx.select_set(0)

    def get_selection(self):
        items = self.lsbx.curselection()
        if items:
            sel = self.lsbx.get(items[0])
            return sel
        else:
            return None


