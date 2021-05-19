#CFD Plotter
#Takes an .sgr file and a 'site' file to create a +/-1200bp region of the reads for each gene in the site file
#Also creates a normalised cumulative frequency distribution which can be used to plot a CFD plot in excel 
#Used as 'python CFD_plotter' from local command line 
#requires:
    #.sgr file in folder sgr_in
    #site file in folder site_in
    #out folder

#####Optional alterations
# # -Change the rounding method (This current script is using 5 and above rounded up with below 5 rounded down)
    #-Not amazingly influential on the end result 
# # -Add options for bin window (currently +/-120)
    #-would just need to set a variable as n in the slice window 
        #-also potentually as a command line argument (but that sounds tedious to input every time)
#Make the output file include the total sum and normalisation values?
        


#import modules 
import pandas as pd 
import os 
import warnings             #Using this is unnecessary but makes it look cleaner
import math
#Remove the futurewarnings for array compaison to str
warnings.simplefilter(action='ignore',category=FutureWarning)

#Find the files 
sgr_files = [file for file in os.listdir('sgr_in') if file.endswith('.sgr')]
site_files = os.listdir('site_in')[0]
normalised_out=''                           #Idea is to make end normalised file all the files together
all_normalised_together =pd.DataFrame()
#open site file rounded to the nearest multiple of 10 (rounding method chosen here)
site_input = pd.read_csv('site_in\\' +site_files, delimiter ='\t',header=None,names=['chr','gene','site','strand'])   


site_input.loc[:,'site'] = site_input.loc[:,'site'].apply(lambda x: (x+5)/10).apply(math.floor).apply(lambda x: x*10)   #Preferable 5 up method as not affected by floats

print(f'''The site file {site_files} is being used
Contains: {(site_input.loc[:,'strand'] == 'F').sum()} Forward strands and {(site_input.loc[:,'strand'] == 'R').sum()} Reverse strands ''')


for file in sgr_files:
    print (f'-----------------------------   \nCurrently working with {file} ')
    
#Create paths and open files 
    sgr_input = pd.read_csv('sgr_in\\' +file,delimiter='\t',header=None,names=['chr','site','reads'])
    out_file = 'out//'+file
    if normalised_out != '':
        normalised_out = normalised_out +'___' +file
    else:
        normalised_out = normalised_out +file
    #Forward and reverse strands made into opposite index arrays (121 is the 0 value)
    #columns are specific genes, rows are reads at a particular distance from the site of that gene 
    #First put into a list of Series as list.append is much more effiecent than pd.concat
    collection_F = []
    collection_R = []  
    
    
    print (f'''Contains {sgr_input.chr.count()} bin values
Contains {len(sgr_input.loc[:,'chr'].unique())} chromosomes ''')
    
    #Changing the chromosome slices to within a hash table 
    chromosomes={}
    for chrom in sgr_input.chr.unique():
        chromosomes.update({chrom:sgr_input[sgr_input.chr== chrom]})

    #Iterate over each gene in site_input and find its location in the sgr file
             
    for gene_index in range(site_input.index.size):
        # print ('working with {} at number {}/{}'.format(site_input.iloc[gene_index,1],gene_index,site_input.index.size))    #Use while still slow
        
        
    #Specify which chromosome the current gene uses  
        specific_chr = chromosomes[site_input.iloc[gene_index,0]]
        
        
        ## Get the index for the site within the specified chromosome indices 
        
        index_reads = specific_chr.index[specific_chr.site == site_input.iloc[gene_index,2]]        
        
        #Create a series with number of reads corresponding to the distance from the site (-1200 is index 0, 0 is index 121, 1200 is index 240)
     
        bin_reads = pd.Series(specific_chr.loc[index_reads[0]-120:index_reads[0]+120,'reads'])    
        
        bin_reads.name = site_input.iloc[gene_index,1]              #Make the column the genes name 
        
        #Concatinate bin_reads collumns with the appropriate collection (forward or reverse strand)
        if site_input.iloc[gene_index,3] == 'F':
            # bin_reads.index = range(1200,-1210,-10)               #Used if index specified in original
            collection_F.append(bin_reads.reset_index(drop=True))
        elif site_input.iloc[gene_index,3] == 'R':
            # bin_reads.index = range(-1200,+1210,10)               #Used if index specified in original
            collection_R.append(bin_reads.reset_index(drop=True))
        else:
            print('Encountered strand direction that is not F or R, this gene will be skipped')
            # break

    #Convert the two collections(lists) of Series to a DataFrame and transpose it 
    collection_F = pd.DataFrame(collection_F).T
    collection_R = pd.DataFrame(collection_R).T
    #Combine the two reads (opposite assignment results in reads being assigned for correct strand 
    
    collection_F.index=range(-1200,1210,10)
    collection_R.index=range(1200,-1210,-10)
    final = pd.concat([collection_F,collection_R],axis=1)
    #Do sum and normalise 
    total_reads = final.sum(axis=1).sum()
    normalisation=total_reads/241
    after_sum_normalised =final.sum(axis=1)/normalisation
    after_sum_normalised.name=file
    print(f'The total amount of reads are {total_reads}\nThe normalisation number is {normalisation}')
    #Save the file output (Temp) 
    final.to_csv(out_file,sep='\t')                                 ###
    # after_sum_normalised.to_csv(normalised_out,sep='\t')
    all_normalised_together = pd.concat([all_normalised_together,after_sum_normalised],axis=1)
    # np.savetxt(out_file,final,delimiter='\t',fmt='%s')
    
all_normalised_together.to_csv('out//normalised_' + normalised_out,sep='\t')   
print('Finished')