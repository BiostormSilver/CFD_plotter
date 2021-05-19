# CFD_plotter
Cumulative distribution plotter which is a program designed to find the cumulative read frequencies across given genomic sites. It uses .sgr files located in a Sgr_in folder and site files located in a Site_in folder with outputs produced in an Out folder. 

The Sgr_in files require the columns (no header):
- Chromosome
- location
- Number of reads

The Site_in file requires  the columns (no header):
- Chromosome
- Gene name
- Site (bp position)
- Read direction (F or R)

The chromosome naming convention needs to match in the Sgr and Site file inputs 
