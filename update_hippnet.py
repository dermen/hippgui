# coding: utf-8
import pandas
import numpy as np


def recompute_gx_gy(df, cornerVar):
    """
    If mergine a different census
    it might be important to recompute
    the gx and gy values as they are rounded
    from the never-changing x,y coords

    Also, the plot corner defitions might changes, so 
    its best to merge on a set plot corner defitions 
    defined once per merge-group
    """
    if cornerVar == 'Palamanui':
        censusx0000 = 185950.  # UTM longitude (I think)
        censusy0000 = 2185420.  # UTM lattitude (I think)
    elif cornerVar == 'Laupahoehoe':
        censusx0000 = 260420.
        censusy0000 = 2205378.
    elif cornerVar == 'Sanctuary':
        censusx0000 = 198451.
        censusy0000 = 2183419.
    elif cornerVar == 'Mamalahoa':
        censusx0000 = 201314.
        censusy0000 = 2192168.
    elif cornerVar == "Palau":
        censusx0000 = 456549.
        censusy0000 = 830137.
        
    nn = df.notnull()
    df.loc[nn['x'], 'gx']  = \
        np.round(df.loc[nn['x'],'x'] - censusx0000, decimals=3)
    df.loc[nn['y'], 'gy']  = \
        np.round(df.loc[nn['y'],'y'] - censusy0000, decimals=3)

    return df


# ---ARGS ----
name = "pln_wide"  # new name for the individual census pickle files
cornerVar = "Palamanui"  # name specifying the corner of the plot (see function def above)
master_fname = "Palamanui_master.txt"  # census data for the previous years are stored in this format
#new_census_pkl = "../../hippgui/MamaJune8th.pkl"  # the new census data after running it through the GUI (pkl file)
#new_census_pkl = "../../hippgui/sanctuary_4.pkl"  # the new census data after running it through the GUI (pkl file)
new_census_pkl = "PalJune8th_droppedNullStat.pkl"
# ----------


df = pandas.read_csv(master_fname, sep='\t')
d_new = pandas.read_pickle(new_census_pkl)
u_id = df.CensusID.unique()
dfs = {i:df.query("CensusID==%d"%i) for i in u_id}

new_files = []
fix_files = []
merge_cols = [c for c in list(d_new) if not c.startswith('dbh') ] 
merge_cols.append( 'treeID')

merge_dfs = []

for i_cens in u_id:
    d_i = dfs[i_cens].query("status != 'P'")
    u_mstem = d_i.mstem.unique()
    dbh_data = d_i.pivot( columns='mstem', values='dbh',index='treeID')
    dbh_data.reset_index(inplace=True)
    col_remap = {mstem:'dbh_%d'%mstem
        for mstem in u_mstem if mstem !=0 }
    dbh_data.rename( columns=col_remap, inplace=True)
    dbh_data.drop(columns=[0], axis=1, inplace=True   ) # drop the 0 column 

    d_i_mstem0 = d_i.query("mstem==0")

    d_final = pandas.merge( d_i_mstem0, dbh_data, on='treeID')
    d_final.drop(columns=['treeID', 'mstem','location'], axis=1, inplace=True)


    merge_dfs.append( d_final)

drop_col = [l for l in list(d_new) 
    if l not in list(d_final) and not l.startswith('dbh')]

print ("dropping ", drop_col)
#d_new['quadrat'] = map( lambda x:"%04d"%int(x), d_new.quadrat)
d_new.drop( columns=drop_col,
    axis=1,inplace=True)
merge_dfs.append( d_new)


u_id = list(u_id) + [d_new.CensusID.values[0]]
for i_df,i_cens in enumerate(u_id):
    print("\n***********************************")
    print("EDITING DATA FOR CENSUS %d" % i_cens)
    print("************************************")
    d_final = merge_dfs[i_df]

    # recompute gx and gy columns
    # to avoid system-dependent rounding discrepancy
    d_final = recompute_gx_gy(d_final, cornerVar)
   
    slp_fix = d_final.query("slp==0")
    if len(slp_fix) > 0:
        print("Found %d values with 0 in the SLP col" % len(slp_fix))
        d_final.loc[slp_fix.index, "slp"] = np.nan
    
    substr_fix = d_final.query("substrate==0")
    if len(substr_fix) > 0:
        print("Found %d values with 0 in the substrate col" % len(substr_fix))
        d_final.loc[substr_fix.index, "substrate"] = np.nan

    if "pig_damage" in list(d_final):
        pig_fix = d_final.loc[ ~d_final.pig_damage.isin([0,1,2,3])]
        if len( pig_fix):
            print("Found %d values with pig damage values not in [0,1,2]" % len(pig_fix))
            d_final.loc[pig_fix.index, "pig_damage"] = np.nan

    d_final.loc[d_final.hom.isnull(), 'hom'] = 130
    d_final.loc[d_final.pom.isnull(), 'pom'] = 130

    # double check the status cols
    for col in ["RawStatus", "status", "DFstatus"]:
        # TODO: these checks need to be in GUI_standardize_hippnet
        # i.e in the main GUI!
        if col not in d_final:
            continue
        
        while 1: #usr_reply != "OK":
            print("\n#######################")
            print("Unique values in %s col:" % col)
            print d_final[col].unique()
            usr_reply = raw_input("To edit a value please enter OLD,NEW  or press ENTER to proceed: \n" )
            if usr_reply == "":
                break
            else:
                old_val, new_val = usr_reply.split(",")
                old_val = old_val.strip()
                new_val = new_val.strip()
                print("For col %s I will replace all instances of %s with %s" % (col, old_val, new_val))
                ok = raw_input("Ok ? (y,n)" )
                while ok not in ["y", "n"]:
                    ok = raw_input("Ok ? (y,n)" )
                if ok == 'y':
                    d_final.loc[ d_final[col] == old_val, col] = new_val 
                break

    # if tree is dead, number of stems should be 0
    nstem_fix = d_final.query("status=='D'").query("nostems > 0")
    if len(nstem_fix) > 0:
        print("Setting nstems=0 where tree was dead for %d trees" % len(nstem_fix))
        d_final.loc[ nstem_fix.index, 'nostems' ] = 0

    dbh_fix = d_final.query("dbh < 1").query("status=='A'")
    if len(dbh_fix) > 0:
        print("Found dbh < 1 for %d alive trees" % len(dbh_fix))
        dbh_fix_file = "dbhfix_%s_%d.pkl" % (name, i_cens)
        dbh_fix.to_pickle(dbh_fix_file)
        print("Saved dbh fix data to %s for checking later" % dbh_fix_file)
        fix_files.append( dbh_fix_file)

    #d_final['quadrat'] = map( lambda x:"%04d"%int(x), d_final.quadrat)
    updated_census_pkl = "%s_%d.pkl"%(name,i_cens) 
    new_files.append( updated_census_pkl)
    d_final.to_pickle( updated_census_pkl)
    print("Wrote updated file %s" % updated_census_pkl)
    print

#new_pkl = "%s_%d.pkl"%(name,i_cens+1) 
#d_new.to_pickle( new_pkl)
#print("Wrote pickle file %s containing the latest data" % new_pkl)

print("Please now run the merger with the newly created files!")
for f in new_files:
    print f

print("And please check these files for fixes")
for f in fix_files:
    print f
print("Mahalo.")


