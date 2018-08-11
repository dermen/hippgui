import os
import itertools
try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk

import pandas
import numpy as np

import database_edit
Editor = database_edit.EditorApp


###########################
# RANDOM HELPER FUNCTIONS #
###########################

def launch_editor( df, inds, message=None, edit_cols=[], root_exists=False):
    if not root_exists:
        root = tk.Tk()
    else:
        root = tk.Toplevel()
    editor = Editor(  root, df, inds, edit_cols=edit_cols )
    editor.pack()
    tk.Button( root, text='Finish', command=root.destroy ).pack()
    if message:
        root.title(message)
    root.mainloop()
    return editor.get_df()


def resolve_na(dataframe, column ,message = None):
    inds = pandas.np.where( dataframe[column].isnull() )[0]
    if inds.size:
        dataframe = launch_editor( dataframe, inds, message=message,root_exists=False)
    return dataframe

def getDBHcol(dataframe):
    dbhCols = [ n for n in list(dataframe) if n.startswith('dbh_') ]
    dbhCols = [ int( n.split('dbh_')[-1] ) for n in dbhCols ] 
    return dbhCols

def addDBH_NA( dataframe, maxDBH):
    thisMaxDBH = max( getDBHcol(dataframe) )
    while thisMaxDBH < maxDBH:
        thisMaxDBH += 1
        new_col = 'dbh_%d'%(thisMaxDBH)
        dataframe.ix[:, new_col] = pandas.np.nan
    return 

def assert_not_null(df, cols=['gx','gy','tag','RawStatus', 'status','DFstatus']):
    for col in cols:
        df = resolve_na( df, col, 'resolve na in col %s'%col)
        assert( all(df[col].notnull() ) ) 

def make_locator_col(df,name='locator', plot_x=200):
    """plot_x is length of plot in meters"""
    df[name] = (df.gx*100 + df.gy*100*plot_x*100).astype(int).astype(str)


class GroupRows:
    def __init__(self, master, dupes_df, dfs_j, loc_col): 
        self.master = master
        self.dupes_df = dupes_df
        self.dfs_j = dfs_j.copy()
        self.loc_col = loc_col

        self.group_colors = itertools.cycle( 'gray%d'%x for x in xrange( 60,70) )

        self.grouped_items = []
        self.group_names = self.dfs_j[self.loc_col].tolist()
        self.new_loc_counter = 0
        
        self._make_widgets()
        self._pack_widgets()
        
    def _make_widgets(self):
        self.editor_frame = Editor(self.master, self.dupes_df,
                        edit_cols=['tag','sp','gx','gy','CensusID',
                                    'dbh', 'RawStatus','notes','ExactDate'] )
        self.data_lb = self.editor_frame.lb
        self.row_map = self.editor_frame.rowmap
        self.group_button = tk.Button(self.master,text='Group selection', command=self._group_sel )
        self.errmsg = self.editor_frame.errmsg
        self.delete_var = tk.IntVar(self.master)
        self.delete_cb = tk.Checkbutton(self.master, 
                                text='Delete un-grouped rows',
                                variable=self.delete_var)
        self.done_button = tk.Button(self.master,text='Done grouping', command=self._group_done)
        self.title_lab = tk.Label(self.master,text='Group Similar items using multi selection. Then click "Group Selection"', 
                            wraplength=250, bd=3, background='darkgreen', foreground='white', relief=tk.RAISED )

    def _pack_widgets(self):
        self.title_lab.pack(side=tk.TOP)
        self.editor_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES)
        self.editor_frame.mode_frame.pack_forget()
        self.editor_frame.editorFrame.pack_forget()
        self.delete_cb.pack(side=tk.TOP)
        self.group_button.pack(side=tk.TOP)
        self.done_button.pack(side=tk.TOP)

    def _group_sel(self):
        items = self.data_lb.curselection()
        items_already_grouped = [i for i in items if i in self.grouped_items ]
        
        if items and not items_already_grouped:
            rows = [ self.row_map[i] for i in items ] 
            group = self.dupes_df.ix[ rows, ]

            new_loc = str(self.new_loc_counter)
            while new_loc in self.group_names:
                self.new_loc_counter += 1
                new_loc = str(self.new_loc_counter)
            self.group_names.append( new_loc)
            index = group.index.values 
            self.dfs_j.ix[index,self.loc_col] = new_loc 
            for i in items:
                self.data_lb.itemconfig(i, {'bg':'black'}) #,'fg':'white'} ) 
                self.data_lb.selection_clear(i)
            self.grouped_items += items
        
        elif items_already_grouped:
            self.errmsg('please only select un-grouped items')

    def _group_done(self):
        if self.delete_var.get():
            remaining_items = [ i for i in xrange(self.data_lb.size()) if int(i) not in self.grouped_items ]
            remaining_rows = [ self.row_map[i] for i in remaining_items]
            for row in remaining_rows:
                group = self.dupes_df.ix[ [row], ]
                index = group.index.values 
                self.dfs_j.drop(index, inplace=True)
        self.master.destroy()



class Merge:
    def __init__(self,output_dir='.', output_prefix='test', plot_x=200, plot_y=None, quad_x=None, 
                subquad_x=None, make_beauty=False, make_pkl=False , recalc_subquad=False):
        """class for merging CTFS wide-format databases.
            output_dir: directory to save files
            output_prefix: str prefix to file names
            plot_x: plot east-to-west dimensions in meters
            plot_y: plot south=to=north dimensions in meters
            quad_x: quadrat width in meter
            subquad: subquad width in meter
            make_beauty: boolean, whether to make a beautifl xlsx file
            make_pkl: boolean, whether to make a python binary file"""
 
        self.plot_name = os.path.join( output_dir, output_prefix)
        try: 
            self.writer = pandas.ExcelWriter('%s_report.xlsx'%self.plot_name)
        except ImportError:
            self.writer = None

        self.loc_col = 'location'
        self.plot_x = int(plot_x)
        if plot_y:
            self.plot_y = int(plot_y)
        if quad_x:
            self.quad_x = int(quad_x)
        if subquad_x:
            self.subquad_x = int(subquad_x)

        self.recalc_SQ = recalc_subquad
        self.make_beauty = make_beauty
        self.make_pkl = make_pkl


    def load_dataframes(self, dfs):
        """loads a list of dataframes and runs
            some quality control functions"""
        max_dbh_col = max([max(getDBHcol(df)) for df in dfs] )
        self.max_stems = max_dbh_col + 1
        for df in dfs:
            df.drop_duplicates(inplace=True)
            df.reset_index(drop=True,inplace=True)
            addDBH_NA( df, max_dbh_col )
            assert_not_null(df)
            make_locator_col(df,name=self.loc_col,plot_x=self.plot_x)
        self.dfs_j = pandas.concat( dfs, ignore_index=True) 

    def merge_dfs(self): 
        """sets up a chain of commands to 
            carry out the error correction and
            data merging/melting"""
        self._check_dupe_row()
        self._check_location_dupes()
        self._correct_loc_dupes()
        self._assign_treeID() 
        self._rename_dbh_cols()
        self._nostems_correction()
        self._xy_duplicates()
        self._tag_duplicates()
        self._group_treeID()
        self._tags_changed()
        self._quadrat_correction()
        self._subquad_correction()
        self._out_of_plot_boundary()
        self._species_changed_correction()
        self._missing_and_prior()
        self._melt_mstem_data()
        self._save_everything()

    def _check_dupe_row(self):
        """Check for multiple measurements in same 
            census for same tree"""
        print("Checking for Duplicates...")
        gb_id = self.dfs_j.groupby((self.loc_col, 'tag', 'CensusID'))
        id_dupes = gb_id.size()[ gb_id.size() > 1 ] 
        if np.any(id_dupes):
            id_dupes = id_dupes.reset_index()
            gb = self.dfs_j.groupby( ('tag',self.loc_col))
            dupe_idx = map(tuple,id_dupes[['tag',self.loc_col]] .values)
            dupes = pandas.concat( gb.get_group(idx) for idx in dupe_idx  )
            all_dupe_inds = dupes.index.values
            self.dfs_j = launch_editor(self.dfs_j, all_dupe_inds, 
                                edit_cols=['tag','sp','gx',
                                            'gy','CensusID',
                                            self.loc_col,'dbh', 'notes',
                                            'RawStatus','ExactDate'], 
                                message='Delte duplicate rows',
                                root_exists=False)
        print("\tDone.")

    def _check_location_dupes(self):
        """find where the x,y overlap in a given census"""
        print("Checking for overlapping trees (i n gx,gy)...")
        gb = self.dfs_j.groupby(( self.loc_col, 'CensusID' ))
        gb_sizes = gb.size().reset_index(name='sizes')
        gb_dupes = gb_sizes.loc[gb_sizes.sizes > 1]
        
        if np.any(gb_dupes):
            ulocs = gb_dupes[self.loc_col].unique()
            isin_locs = self.dfs_j[self.loc_col].isin(ulocs)
            
            utags = self.dfs_j.loc[ isin_locs ]['tag'].unique()
            isin_tags = self.dfs_j.tag.isin(utags)
            
            isin =  np.logical_or( isin_locs, isin_tags) 
            self.dupes_df = self.dfs_j.loc[isin]
            self.dupes_df = self.dupes_df.drop_duplicates()
            self.dupes_df = self.dupes_df.sort_values( by=['tag','CensusID'])
        else:
            self.dupes_df = None
        print("\tDone.")
        
    def _correct_loc_dupes(self):
        print("Correcting for duplicates...")
        if self.dupes_df is not None:
            root = tk.Tk()
            group_rows = GroupRows(root, self.dupes_df, self.dfs_j, self.loc_col)
            root.mainloop()
            self.dfs_j = group_rows.dfs_j 
        print("\tDone.")

    def _assign_treeID(self):
        """Assigin the tree ID"""
        print("Assiging unique tree ID based on tag and position...")
        treeID_map = { loc:i for i,loc in enumerate(pandas.unique(self.dfs_j[self.loc_col])) }
        treeID     = [ treeID_map[l] for l in self.dfs_j[self.loc_col] ]
        self.dfs_j.ix[:,'treeID'] = treeID
        print("\tDone.")


    def _rename_dbh_cols(self):
        """rename dbh main stem col"""
        print("Renaming DBH columns for melted format...")
        self.dfs_j.rename( columns={'dbh':'dbh_0'}, inplace=True)
        self.dbh_cols = ['dbh_%d'%x for x in xrange(self.max_stems)] # colums corresponding to the dbh values
        self.dfs_j    = self.dfs_j.ix[:, [c for c in list(self.dfs_j) if c not in self.dbh_cols] + self.dbh_cols] # rearrange the column order for cleanliness
        print("\tDone.")

    def _nostems_correction(self):
        """correct where number of stems is inaccurate"""
        print("Counting number of stems and correcting reported value if necessary...")
        dbh_na_map = {0:np.nan, -1:np.nan, -999:np.nan}
        self.dfs_j.replace(to_replace={c:dbh_na_map for c in self.dbh_cols}, inplace=True)

#       sort the dbh vals so no vals are at the end 
        self.dfs_j.ix[:,['dbh_%d'%x for x in xrange(1,self.max_stems)]] = np.sort( self.dfs_j.ix[:,['dbh_%d'%x for x in xrange(1,self.max_stems)]].values, axis=1)
#       number of recorded stems dbh values VS the number recorded in the 'nostems' columns
        nostems_actual   = self.dfs_j.ix[:,self.dbh_cols].notnull().sum(axis=1)
        nostems_err_inds = np.where( nostems_actual != self.dfs_j.nostems )[0]
        if nostems_err_inds.size:
            subdata = self.dfs_j.iloc[nostems_err_inds].reset_index().set_index(['CensusID','index']).sortlevel(0)
            if self.writer:
                subdata.to_excel( self.writer, 'nostem_mistakes', float_format='%.2f' , na_rep='NA') 
            self.dfs_j.update(nostems_actual.iloc[nostems_err_inds].to_frame('nostems') )
        print("\tDone.")

    def _xy_duplicates(self):
        """list xy duplicates per census"""
        print("Listing xy duplicates.. ")
        xy_groups      = self.dfs_j.groupby(['CensusID','gx','gy'])
        xy_dupe_inds   = [inds for group,inds in xy_groups.groups.iteritems() if len(inds) > 1 ]
        if xy_dupe_inds:
            xy_dupe_inds   = [i for sublist in xy_dupe_inds for i in sublist] # 2d to 1d
            subdata     = self.dfs_j.iloc[xy_dupe_inds].reset_index().set_index(['CensusID','index']).sortlevel(0)
            if self.writer:
                subdata.to_excel( self.writer, 'xy_duplicates', float_format='%.2f' , na_rep='NA') 
        print("\tDone.")


    def _tag_duplicates(self):
        """list tag duplicates per census"""
        print("Listing tag duplicates")
        tag_groups      = self.dfs_j.groupby(['CensusID','tag'])
        tag_dupe_inds   = [inds for group,inds in tag_groups.groups.iteritems() if len(inds) > 1 ]
        if tag_dupe_inds:
            tag_dupe_inds   = [i for sublist in tag_dupe_inds for i in sublist] # 2d to 1d
            subdata     = self.dfs_j.ix[tag_dupe_inds].reset_index().set_index(['CensusID','index']).sortlevel(0)
            if self.writer:
                subdata.to_excel( self.writer, 'tag_duplicates', float_format='%.2f' , na_rep='NA') 
        print("\tDone.")

    def _group_treeID(self):
        self.id_groups = self.dfs_j.groupby( ['treeID'] )


    def _tags_changed(self):
        """list tags that change across censuses"""
        print("Trees where tags have changed...")
        tags_per_treeID = self.id_groups['tag'].unique()
        tags_changed = [ treeID for treeID,tags in tags_per_treeID.iteritems() if len(tags) > 1 ]
        if tags_changed:
            subdata = pandas.concat([ self.id_groups.get_group(treeID) for treeID in tags_changed], keys=tags_changed )
            if self.writer:
                subdata.to_excel( self.writer, 'tags_changed', float_format='%.2f' , na_rep='NA') 
        print("\tDone.")

    def _quadrat_correction(self):
        """correct where quadrat is incorrect"""
        print("Correcting where tree quadrat is out of bounds...")
        if self.quad_x:
            quad = zip( (self.dfs_j.gx/self.quad_x).astype(int), (self.dfs_j.gy/self.quad_x).astype(int) )
            quad_str = map( lambda x: '%02d%02d'%(x[0],x[1]), quad)
            quad_str = pandas.Series(data=quad_str, index=self.dfs_j.index)
            quad_err_inds = np.where( quad_str != self.dfs_j.quadrat )[0]
            if quad_err_inds.size:
                subdata = self.dfs_j.iloc[quad_err_inds].reset_index().set_index(['CensusID','index']).sortlevel(0)
                if self.writer:
                    subdata.to_excel( self.writer, 'quadrat_mistakes', float_format='%.2f' , na_rep='NA') 
                self.dfs_j.update(quad_str.iloc[quad_err_inds].to_frame('quadrat'))
        print("\tDone.")
    
    
    def _subquad_correction(self):
        """correct where subquad is incorrect"""
        if not self.recalc_SQ:
            return
        print("Attempting subquad correction...")
        if self.quad_x and self.subquad_x:
            subquad = zip((self.dfs_j.gx%self.quad_x/self.subquad_x).astype(int)+1, (self.dfs_j.gy%self.quad_x/self.subquad_x).astype(int)+1 )
            subquad_str = map( lambda x: '%d,%d'%(x[0],x[1]), subquad)
            subquad_str = pandas.Series(data=subquad_str, index=self.dfs_j.index)
            #subquad_err_inds = np.where( subquad_str != self.dfs_j.subquad )[0]
            #if subquad_err_inds.size:
            
            subdata = self.dfs_j.iloc[:].reset_index().set_index(['CensusID','index']).sortlevel(0)
                
                #if self.writer:
                #    subdata.to_excel( self.writer, 'subquad_mistakes', float_format='%.2f' , na_rep='NA') 
                
            self.dfs_j.update(subquad_str.iloc[:].to_frame('subquad'))
        print("\tDone.")

    def _out_of_plot_boundary(self):
        """list entries that are out of the plot bounds"""
        print("Listing where x,y is out of bounds")
        if self.plot_x and self.plot_y:
            x_out_inds = np.where( self.dfs_j.gx > self.plot_x )[0]
            if x_out_inds.size:
                subdata = self.dfs_j.iloc[x_out_inds].reset_index().set_index(['CensusID','index']).sortlevel(0)
                if self.writer:
                    subdata.to_excel( self.writer, 'x out of bounds', float_format='%.2f' , na_rep='NA') 
            y_out_inds = np.where( self.dfs_j.gy > self.plot_y )[0]
            if y_out_inds.size:
                subdata = self.dfs_j.iloc[y_out_inds].reset_index().set_index(['CensusID','index']).sortlevel(0)
                if self.writer:
                    subdata.to_excel( self.writer, 'y out of bounds', float_format='%.2f' , na_rep='NA') 
        print("\tDone.")


    def _species_changed_correction(self):
        """find and correct species that change across censuses"""
        print("Where has the species changed; will use most recent assigned species//")
        sp_per_treeID = self.id_groups['sp'].unique()
        sp_changed = [ treeID for treeID,sp_vals in sp_per_treeID.iteritems() if len(sp_vals) > 1 ]
        if sp_changed:
            subdata = pandas.concat([ self.id_groups.get_group(treeID) for treeID in sp_changed], keys=sp_changed )
            if self.writer:
                subdata.to_excel( self.writer, 'sp_changed', float_format='%.2f' , na_rep='NA') 
            for treeID in sp_changed:
                group = self.id_groups.get_group(treeID)
                recent_sp = group.ix[ np.argmax(group.CensusID), 'sp']
                self.dfs_j.ix[group.index.tolist(),'sp' ] = recent_sp
        print("\tDone.")
    
    
    def _missing_and_prior(self):
        """create prior and missing entries for main stems
            in censuses that don't have a recording"""
        print("Making rows for missing and prior trees.. ")
        allcensuses = np.unique( self.dfs_j.CensusID)
        nostem_per_treeID = self.id_groups['nostems'].unique()
        census_per_treeID = self.id_groups['CensusID'].unique()

        myvals = ['gx','gy','x','y','subquad','quadrat','sp','treeID', 'tag']
        id_groups_myvals = self.dfs_j[myvals].reset_index(drop=True).groupby( ['treeID'] )

        records = [] # prior and missing etc
        for tree in np.unique(self.dfs_j.treeID):
            group = id_groups_myvals.get_group(tree) # slow part, but I cannot speed it up
            vals = group.iloc[0].to_dict() # another slow part...
            
            censuses = census_per_treeID[tree]
            where_new = censuses.min() 
            new_items = [ (key,vals[key]) for key in myvals ]

            new_censuses = np.setdiff1d( allcensuses, censuses) 
            prior = new_censuses[ new_censuses < where_new] 
            missing = new_censuses[ new_censuses > where_new] 

            for c in prior:
                records.append(dict(new_items+[('CensusID',c),('RawStatus', 'prior')]) )
            for c in missing:
                records.append(dict(new_items+[('CensusID',c),('RawStatus', 'missing')]) )

        new_data = pandas.DataFrame.from_records(records)
        self.data = pandas.concat((self.dfs_j, new_data),ignore_index=True)
        self.data.loc[ self.data.RawStatus=='missing',['DFstatus','status'] ] = 'missing','M'
        self.data.loc[ self.data.RawStatus=='prior',  ['DFstatus','status'] ] = 'prior','P'
        print("\tDone.")
    
    
    def _melt_mstem_data(self):
        """melt the mstem data from wide to long format"""
        print("MELT Multiple stem data")
        nostems_max = self.data.groupby('treeID')['nostems'].max()
        melted_data = []
        id_vars = [c for c in list(self.dfs_j) if c not in self.dbh_cols] 
        for n in np.unique(nostems_max).astype(int):
            trees = nostems_max.loc[ nostems_max==n].index.values
            subdata = self.data[self.data.treeID.isin(trees) ]
            melted = pandas.melt( subdata, value_vars=self.dbh_cols[:n] , 
                                    var_name='mstem', value_name='dbh', id_vars=id_vars)
            melted_data.append(melted)

        self.tidy_data = pandas.concat( melted_data, ignore_index=True)
        self.tidy_data.ix[:,'mstem'] = self.tidy_data.ix[:,'mstem'].map( lambda x:x.split('_')[-1] )
    
        self.tidy_data = self.tidy_data.sort_index(by=['treeID','CensusID'])
        print("\tDone.")

    def _save_everything(self):
        print("Saving...")
        self.tidy_data.to_csv('%s_master.txt'%self.plot_name, sep='\t', na_rep='NA', float_format='%.2f')
        if self.writer:
            print("\tSaving XCEL datalog marking changes..")
            self.writer.save()
        if self.make_pkl:
            print("\tSaving pickle...")
            self.tidy_data.to_pickle('%s_stacked.pkl'%self.plot_name)
        if self.make_beauty:
            print("\tSaving formatted XCEL")
            beautiful_data = self.tidy_data.groupby(('treeID','CensusID','mstem')).first()
            beautiful_data.to_excel( '%s_beauty.xlsx'%self.plot_name, na_rep='NA', float_format='%.2f')
        print("\tDone.")


if __name__ == '__main__':
    pkl_dir = '/Users/mender/Desktop'
    plot_name = 'Lau_check'
#   plot_name = 'Pal_check'
#   plot_name = 'Mam_check'
#   plot_name = 'Sanc_check'
    yrs = [2009,2010,2011,2012,2013]
    pkl_files = [os.path.join( pkl_dir, '%s_%d.pkl'%(plot_name,yr)) for yr in yrs ] 
    dfs = [ pandas.read_pickle(pkl_f) for pkl_f in pkl_files ]
    opts = {'plot_x': 200,
            'plot_y': 200,
            'quad_x': 20,
            'subquad_x': 5}
    merge = Merge(**opts)
    merge.load_dataframes(dfs)
    merge.merge_dfs()

