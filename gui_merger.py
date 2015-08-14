import os
try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk
import tkFileDialog

import pandas

import gui_merger_helper

class Merger(tk.Frame):
    def __init__(self, master, *args, **kwargs):
        tk.Frame.__init__(self,master,*args,**kwargs)
        
        self.main_frame = tk.Frame(self)
       
        self.master = master

        self.btn_frame = tk.Frame( self.main_frame, bd=2, relief=tk.RIDGE)
        self.sel_btn = tk.Button(self.btn_frame,
                                text='select files to merge', 
                                command=self._sel_files,
                                relief=tk.RAISED, bd=3)
        self.clear_btn = tk.Button(self.btn_frame, 
                                   text='clear selected files', 
                                   command=self._clear_selection,
                                   relief=tk.RAISED, bd=3)
        self.open_files_btn = tk.Button(self.btn_frame,
                                            text='Merge files',
                                            command=self._open_and_merge,
                                            relief=tk.RAISED, bd=3)
        self.filenames = []
        self.file_list = tk.Listbox(self.main_frame, bd='3',relief=tk.SUNKEN)
        self._add_listbox_title()
        self._pack_widgets()


    def _sel_files(self):
        file_opt = {'filetypes': [],
                    'initialdir': os.path.expanduser('~')}
        filenames = tkFileDialog.askopenfilenames(**file_opt)
        self.filenames = list(set( filenames).union(self.filenames))
        self._list_files()

    def _clear_selection(self):
        self.filenames = []
        self.file_list.delete(0,tk.END)
        self._add_listbox_title()

    def _add_listbox_title(self):
        self.file_list.insert(tk.END,"Currently Selected Files:")
        self.file_list.itemconfig(0,{'background':'darkgreen','foreground':'white'} )

    def _list_files(self):
        self.file_list.delete(0,tk.END)
        self._add_listbox_title()
        for fname in self.filenames:
            self.file_list.insert(tk.END,fname)
        self.file_list.selection_clear(0,tk.END)
    
    def _pack_widgets(self):
        self.main_frame.pack(fill=tk.BOTH,expand=tk.YES)
        
        self.btn_frame.pack( side=tk.TOP) 
        self.file_list.pack(side=tk.TOP,fill=tk.BOTH,
                            expand=tk.YES, padx=5, pady=5)
        
        self.sel_btn.pack(side=tk.LEFT, expand=tk.YES)
        self.clear_btn.pack(side=tk.LEFT, expand=tk.YES)
        self.open_files_btn.pack(side=tk.LEFT,expand=tk.YES)
        
    def _open_and_merge(self):
        self.dfs  = []
        if len( self.filenames)<2:
            self.errmsg('Please select at least 2 files!')
            return
    
        for fname in self.filenames:
            if fname.endswith('.pkl'):
                try:
                    df = pandas.read_pickle(fname)
                except Exception as err:
                    self._errmsg(message=err)
                    self.clear_selection()
                    self.dfs = []
                    return
            elif fname.endswith('.xlsx'):
                try:
                    df = pandas.read_excel(fname)
                except Exception as err:
                    self._errmsg(message=err)
                    self.clear_selection()
                    self.dfs = []
                    return
            else:
                self._errmsg(message='Please only select ".xlsx" or ".pkl" files.')
                self.clear_selection()
                self.dfs = []
                return
            self.dfs.append(df)
       
        self._get_plot_x()

    def _get_plot_x(self):
        self.plot_x_win = tk.Toplevel()
        self.plot_x_win.title('Merger info (plot dimensions and output preferences)')
       
        self._east_west()
        self._south_north()
        self._quad_width()
        self._subquad_width()
        self._output_prefix()
        self._extra_outputs()
        self._change_where_save()
        self._done_button()

    def _east_west(self):
        tk.Label(self.plot_x_win, text='Enter width of plot (East-West) in meters:').grid(row=0,column=0)
        self.plot_x_entry = tk.Entry(self.plot_x_win)
        self.plot_x_entry.grid(row=0,column=1,sticky=tk.W)
        
    def _south_north(self):
        tk.Label(self.plot_x_win, text='Enter width of plot (South-North) in meters:').grid(row=1,column=0) 
        self.plot_y_entry = tk.Entry(self.plot_x_win)
        self.plot_y_entry.grid(row=1,column=1,sticky=tk.W)
        
    def _quad_width(self):
        tk.Label(self.plot_x_win, text='Enter width of quadrat in meters:').grid(row=2,column=0)
        self.quad_x_entry = tk.Entry(self.plot_x_win)
        self.quad_x_entry.grid(row=2,column=1,sticky=tk.W)
        
    def _subquad_width(self):
        tk.Label(self.plot_x_win, text='Enter width of subquad in meters:').grid(row=3,column=0)
        self.subquad_x_entry = tk.Entry(self.plot_x_win)
        self.subquad_x_entry.grid(row=3,column=1,sticky=tk.W) 

    def _output_prefix(self):
        tk.Label(self.plot_x_win, text='Enter an output file prefix:').grid(row=4,column=0)
        self.out_pref_entry = tk.Entry(self.plot_x_win)
        self.out_pref_entry.grid(row=4,column=1,sticky=tk.W) 

    def _extra_outputs(self):
        self.beauty_var = tk.IntVar(self.plot_x_win)
        beauty_cb = tk.Checkbutton(self.plot_x_win, text='Save pretty xlsx (for data viewing)', 
                                        variable=self.beauty_var ) 
        beauty_cb.grid(row=5,column=0,sticky=tk.W)
        
        self.pkl_var = tk.IntVar(self.plot_x_win)
        pkl_cb = tk.Checkbutton(self.plot_x_win, text='Save pickle binary (for python analysis)', 
                                        variable=self.pkl_var ) 
        pkl_cb.grid(row=5,column=1,sticky=tk.W)

    def _change_where_save(self):
        btn = tk.Button( self.plot_x_win, text='Output directory (click to change):', relief=tk.SOLID, 
                    bd=3, command=self._change_out_dir)
        btn.grid(row=6, column=0,sticky=tk.W)
        self.out_dir = os.path.dirname( self.filenames[0] )
        self.out_dir_lab = tk.Label(self.plot_x_win, text=self.out_dir)
        self.out_dir_lab.grid(row=6, column=1)

    def _done_button(self):
        tk.Button(self.plot_x_win, text='Done', command=self._set_plot_x).grid(row=7, columnspan=2)
        
    def _set_plot_x(self):
        self.plot_x = self.plot_x_entry.get()
        self.plot_y = self.plot_y_entry.get()
        self.quad_x = self.quad_x_entry.get()
        self.subquad_x = self.subquad_x_entry.get()
        self.out_pref = self.out_pref_entry.get()
        self.make_beauty = bool( self.beauty_var.get() )
        self.make_pkl = bool( self.pkl_var.get() )

        self.master.destroy()
        
        merger_args = { 'plot_x':self.plot_x, 'plot_y':self.plot_y,
                        'quad_x':self.quad_x, 'subquad_x':self.subquad_x,
                        'output_prefix':self.out_pref, 'output_dir':self.out_dir,
                        'make_beauty':self.make_beauty, 'make_pkl':self.make_pkl }
        merge = gui_merger_helper.Merge(**merger_args)
        merge.load_dataframes(self.dfs)
        merge.merge_dfs()

    def _errmsg(self, message):
        """ opens a simple error message"""
        errWin = tk.Toplevel()
        tk.Label(errWin, text=message, foreground='white', background='red' ).pack()
        tk.Button( errWin,text='Ok', command=errWin.destroy ).pack()
    
    def _change_out_dir(self):
        askdir_opt = {}
        askdir_opt['mustexist'] = False
        askdir_opt['parent'] = self.plot_x_win
        askdir_opt['initialdir'] = os.path.expanduser('~')
        self.out_dir = tkFileDialog.askdirectory(**askdir_opt)
        self.out_dir_lab.config(text=self.out_dir)

def main():
    root = tk.Tk()
    merger_frame = Merger(root)
    merger_frame.pack(fill=tk.BOTH, expand=tk.YES)
    root.mainloop()

if __name__ =='__main__':
    main()    
