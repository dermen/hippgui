try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk

import pandas

import database_edit
from helper import ScrollList
EditorApp  = database_edit.EditorApp

class ResolveData(tk.Frame):
    def __init__(self, master, dataframe, edit_this_col=None):
        """ This class resilves errors in a dataframe column
            by allowing the user to inspect the data in that column.
            master: parent widget
            dataframe: a pandas.Data.Frame object
            edit_this_col: str, name a a column to edit by default"""
        tk.Frame.__init__(self, master, bd=3, relief=tk.RIDGE)
        self.master  = master

#       the dataframe
        self.df_orig = dataframe.copy()
        self.df      = dataframe
        
        self.b_opt = {'bd':4,'relief':tk.RAISED}
        self.frame_opt = {'bd':2, 'relief':tk.RIDGE}

        self.topframe = tk.Frame( self) #, width=300, height=200)
        self.topframe.pack(expand=tk.YES, fill=tk.BOTH) #fill=tk.BOTH,expand=tk.YES)

        self.working_frame = tk.Frame( self.topframe) #, width=300, height=200)
        self.working_frame.pack()

#       option menu for selection of dataframe column to resolve
        self.init_lab = tk.Label(self.working_frame,text='Select a column to edit', foreground='white', background='darkgreen')
        self.opt_var = tk.StringVar(self.working_frame)
        self.opt = tk.OptionMenu( self.working_frame, self.opt_var, *list(self.df) )
        self.opt_var.set(list(self.df)[0])

        if edit_this_col:
            if edit_this_col in self.df:
                self.opt_var.set(edit_this_col)
                self._col_select()
            else:
                raise ValueError
        else:
#           make button for selecting column and spawning the next set of widgets
            self.sel_b = tk.Button(self.working_frame, text='Select', command = self._col_select )
            self._grid_init()
    def _grid_init(self):
        self.init_lab.grid(row=0,column=0)
        self.opt.grid(row=0, column=1)
        self.sel_b.grid(row=1, columnspan=2)
     
    def _col_select( self):
        self.col = self.opt_var.get() 
        if self.col not in list(self.df):
            return
        else:
            self._start()
    
    def _start(self, reset_df=False):
        self.topframe.destroy() 
        self.topframe = tk.Frame( self) #, width=300, height=200)
        self.topframe.pack(fill=tk.BOTH,expand=tk.YES)
        if reset_df:
            self.df = self.df_orig.copy() 
        
        self._set_unique_and_null_vals()
        self._frame_uval_list()
        self._frame_interact()
        self._pack_frames()
  
    def _set_unique_and_null_vals(self):
        """ determine the unique values in data 
            column and store them in a dict"""
        self.unique_vals = {}
        
        where_ = pandas.np.where
        df_col = self.df[self.col]
        u_vals = pandas.unique( df_col[ df_col.notnull() ] )
        
        for val in u_vals:
            self.unique_vals[val] = where_( df_col==val)[0]
   
        null_inds = where_(self.df.isnull()[self.col]) [0]
        if null_inds.size:
            self.unique_vals['NULL__'] = null_inds 

#######################
# SIDE-BY-SIDE FRAMES #
#######################
    def _frame_uval_list(self):
        self.ls_frame = ScrollList(self.topframe, **self.frame_opt )
        self.ls_frame.fill(lines=self.unique_vals.keys())
    
    def _frame_interact(self):
        self.win_inter = tk.Frame(self.topframe, **self.frame_opt) 
        tk.Label(self.win_inter, text='Enter new value:', bg='darkgreen',fg='white').grid(row=0,column=0)
        self.new_val = tk.Entry(self.win_inter)
        self.new_val.grid(row=0,column=1)
        tk.Button(self.win_inter, text='replace all', command=self._replace_data, **self.b_opt).grid(row=2,columnspan=2)
        tk.Button(self.win_inter, text='resolve data', command=self._resolve_data, **self.b_opt).grid(row=3,columnspan=2)
        tk.Button(self.win_inter, text='remove all', command=self._remove_data, **self.b_opt).grid(row=4,columnspan=2)
        self.reset_b = tk.Button( self.win_inter, text='Reset', command=lambda :self._restart(reset_df=True), **self.b_opt)
        self.reset_b.grid(row=5,columnspan=2)

    def _pack_frames(self):
        self.ls_frame.pack(side=tk.LEFT, expand=tk.YES, fill=tk.BOTH)
        self.win_inter.pack(side=tk.LEFT, expand=tk.YES, fil=tk.BOTH)

#######################
# INTERACTION BUTTONS #
#######################
    def _replace_data(self):
        col_val = self.ls_frame.get_selection()
        if not col_val:
            return
        new_val = self.new_val.get() 
        if new_val != col_val:
            inds = self.unique_vals[col_val]
            col_type = self.df.dtypes[self.col]
            self.df.ix[inds, self.col] = pandas.np.array([new_val], dtype=col_type)[0]
        self._restart()

    def _resolve_data(self):
        col_val = self.ls_frame.get_selection()
        if not col_val:
            return
        rows = self.unique_vals[col_val]
        self.resolve_win  = tk.Toplevel()
        self.editor_frame = EditorApp( self.resolve_win , self.df, rows, set_col=self.col )
        self.editor_frame.pack()
        b = tk.Button(self.resolve_win, text='Done', command=self._resolve_data_done)
        b.pack(side=tk.LEFT,fill=tk.BOTH)
             
    def _resolve_data_done(self):
        self.resolve_win.destroy()
        self.df = self.editor_frame.get_df()
        self._restart()

    def _remove_data(self):
        col_val = self.ls_frame.get_selection()
        if not col_val:
            return
        rows = self.unique_vals[col_val] 
        if rows.size:
            self.df.drop(self.df.index[rows], inplace=True)
            self.df.reset_index(drop=True, inplace=True)
        self._restart()

    def _restart(self, reset_df=False):
        self._start(reset_df)
    

if __name__ == '__main__':
    df     = pandas.DataFrame( {'model': pandas.np.random.randint( 0,3,30), 'param1': pandas.np.random.random(30).round(3), 'param2': pandas.np.random.random(30).round(3)} )
    root   = tk.Tk()
    editor =  ResolveData(root, df)
    editor.pack(fill=tk.BOTH,expand=tk.YES)
    #tk.Button( root, text='Exit', command=root.destroy).pack(side=tk.BOTTOM)
    root.mainloop()
