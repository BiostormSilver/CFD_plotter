# Import dash modules
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate


# Import other modules
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd 
import math
import base64
import io



app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Tab styles
# ~ used in dcc.Tabs and dcc.Tab
tabs_styles = {"height": "44px"}
tab_style = {"borderBottom": "1px solid #d6d6d6", "padding": "6px"}

tab_selected_style = {
    "borderTop": "1px solid #d6d6d6",
    "borderBottom": "1px solid #d6d6d6",
    "backgroundColor": "#b6cefc",
    "color": "black",
    "padding": "1px",
}

# Text for the info page
input_info = """
### Input files
The Cumulative frequency distribution plotter (CFD) takes as its input one or more .sgr files and a single site file. 
##### sgr files
The .sgr file needs the .sgr extention and to have the following columns:
* Chromosome
    * In theory any chromosome naming convention can be used as long as they match the site file being used
* bin/position
    *   SAM2PartN_sgr_full script 
* Number of reads within that bin
    * I belive this was made using a 3 bin moving average

##### Site files
The site files can have any extention (I probably should restrict that) and needs the following columns:
* Chromosome
    * Needs to match the sgr files
    * It will probably error if the sgr files have a chromosome that isn't represneted in the site file
* Gene name
    * This can be pretty much anything, its mostly a placeholder
* Position 
    * The genomic position of the sites you want to investigate 
    * E.g. TSS of genes 
* Strand
    * The strand the item (each row) is on 
    * Currently only accepts F or R notation 
        * *Will update that at some point*
    * Also you currently need to have at least one forward and reverse stranded item
        * *Also will update this*

"""
mechanism_info="""
### How the CFD plotter functions
Its something like:\n
1. Reads in the site file and rounds to the nearest multiple of 10
	* This allows the site to be matched in the sgr file
2. Creates a large for loop iterating over sgr files
3. Slices the sgr file into seperate columns within a dictionary (hash table)
	* This speeds up the processing
4. Iterates over each row in the site file
	* Determines the chromosome being used in the current iteration
	* Finds the index that the site matches to within the chromosome 
	* Creates a +/- 120 index window (1200 bp) and identifies the number of reads within each bin for that site
    * These are appended to a forward or reverse strand list and the loop continues creating a large list of every site +/- 1200bp 
5. The forward and reverse list are combined so that the strand direction is accounted for
6. The normalisation value is calculated from the total number of reads divided by the bin window size (241)
7. The total sum of each bin is divided by the normalisation value to give the final values for each bin

I can give no guarantee that this app will actually work or that whatever is produced has any meaning

"""

other_info ="""
### Known Issues
* Fails if the site file has either no Forward or no reverse Strand items
* Only checks if the column length is correct, if the data within it is misordered then it'll try and fail to run
    * This is to prevent the code disabling the button when the data might work but should probably be altered 
* The files are "checked" when they are loaded which would be slow with many files 
* It seems to get stuck when inputting data sometimes and I'm not sure why

### Potentually adding
Writing this on the actual app for a sense of emposing urgency
* Fix the known issues
    * Totally
* Make the info page either collapsible or searchable
    * Just make it easier to navigate when you inevitably make it overly complicated
* Give info on the files loaded? 
    * The process already calculates bin values, chromosomes, total reads and normalisation value; These could just be returned
* Give options for bin size 
* Now we know how to share across callbacks the two inputs should have seperate callbacks
    * !!!!!!!!!!!!
    * It'll go so much smoother 

### Added 
* 10/05/2021 - Download button for the normalised output data produced 
    * Output from the main callback is stored in an object and then shared to the download callback
    * Download callback is prevented from updating on load in to reduce the number of accidental downloads of nothing
    * Functioning of the code could be improved 
"""



app.layout = html.Div(
    [
        dbc.Tabs(
            [
                #Tab 1 Test site
                dbc.Tab(
                    label="CFD",
                    children=[
                        #Row 1
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.H3(
                                        "CFD Plotter",
                                        style={
                                            "font-size": "20px",
                                            "margin-top": "10px",
                                        },
                                    ),
                                    width={"size": "auto"},
                                    align="center",
                                )
                            ],
                            justify="center",
                            align="center",
                        ),
                        #Row 2
                        dbc.Jumbotron(
                            dbc.Row(
                                [
                                    #Column 1
                                    dbc.Col(
                                        [
                                            html.Div(
                                                "SGR Input", style={"margin-left": "10px", "margin-top": "5px", "text-align": "center"}
                                            ),
                                            html.Hr(),
                                            dcc.Upload(
                                                id='upload-data',
                                                children=html.Div([
                                                    'Drag and Drop or ',
                                                    html.A('Select Files')
                                                ],),
                                                style={
                                                    'width': '90%',
                                                    'height': '60px',
                                                    'lineHeight': '60px',
                                                    'borderWidth': '1px',
                                                    'borderStyle': 'dashed',
                                                    'borderRadius': '10px',
                                                    'textAlign': 'center',
                                                    'margin': '10px'
                                                },
                                                # Allow multiple files to be uploaded
                                                multiple=True
                                            ),
                                            dbc.Spinner( 
                                                children = [                                            
                                                    html.Div(
                                                        id="SGR_file_text",
                                                        children="None",
                                                        style={'whiteSpace': 'pre-line'}
                                                    )
                                                ],
                                                type="border",
                                                color="black",
                                                size="md",                                                
                                            ),
                                            
                                        ],
                                        width={"size":6},
                                    ),
                                    #Column 2
                                    dbc.Col(
                                        [
                                            html.Div(
                                                "Site Input", style={"margin-left": "10px", "margin-top": "5px", "text-align": "center"}
                                            ),
                                            html.Hr(),
                                            dcc.Upload(
                                                id='upload-sites',
                                                children=html.Div([
                                                    'Drag and Drop or ',
                                                    html.A('Select Files')
                                                ],),
                                                style={
                                                    'width': '90%',
                                                    'height': '60px',
                                                    'lineHeight': '60px',
                                                    'borderWidth': '1px',
                                                    'borderStyle': 'dashed',
                                                    'borderRadius': '10px',
                                                    'textAlign': 'center',
                                                    'margin': '10px'
                                                },
                                            ),
                                            dbc.Spinner( 
                                                children = [
                                                    html.Div(
                                                        id="Site_file_text",
                                                        children="None",
                                                        style={'whiteSpace': 'pre-line'}
                                                    ),
                                                ],
                                                type="border",
                                                color="black",
                                                size="md",
                                            ),
                                            
                                        ],
                                        width={"size":6},
                                    ),
                                ]
                            ),
                            style={
                                "margin": "auto",
                                "padding": "10px",
                                "margin-top": "10px",
                            }
                        ),
                        dbc.Row(
                            dbc.Col(
                                [
                                    html.Br(),
                                    dbc.Button(
                                        "Update",
                                        id="update_button",
                                        n_clicks = 0,
                                        disabled=False,
                                        color="secondary",
                                        size= "lg"
                                    )
                                ]
                            )
                        ),
                        dbc.Row(
                            dbc.Col(
                                [
                                    dbc.Spinner(
                                        children = [
                                            dcc.Graph(id="graph"),
                                        ],
                                        type="border",
                                        color="black",
                                        size="lg",
                                       # fullscreen=False
                                    ),
                                ]
                            ),
                        ),
                        dbc.Row(
                            dbc.Col(
                                [
                                    dbc.Button(
                                        "Download data",
                                        id="download_button",
                                        n_clicks = 0,
                                        disabled=False,
                                        color="secondary",
                                        size= "lg",
                                    ),
                                    dcc.Store(id="Stored_df"),
                                    dcc.Download(id="download_df"),
                                ]
                            )
                        ),
                                    
                        
                    ],
                    style=tab_style,
                    active_tab_style=tab_selected_style
                ),
                #Tab 2
                dbc.Tab(
                    label="Info",
                    children=[
                        #Row 1
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.H3(
                                        "Info Page",
                                        style={
                                            "font-size": "20px",
                                            "margin-top": "10px",
                                        },
                                    ),
                                    width={"size": "auto"},
                                    align="center",                    
                                )
                            ],
                            justify="center",
                            align="center",
                        ),
                        #Row 2
                        dbc.Jumbotron(
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                                dcc.Markdown(
                                                    input_info
                                                ),
                                                dcc.Markdown(
                                                    mechanism_info
                                                ),
                                                dcc.Markdown(
                                                    other_info
                                                ),

                                                
                                                
                                                
                                        ],
                                        width ={
                                            "size":12
                                        }
                                            
                                    )
                                ]
                            ),                     
                            style={
                                "margin": "auto",
                                "padding": "10px",
                                "margin-top": "10px",
                                "margin-left": "10px",
                                "margin-right": "10px"
                            },
                        
                        )   
                    ]
                )
            ]
        )
            
    ]
)
                                        
###Define functions to use in the callbacks


def parse_contents(contents, filename,site=False):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    if site == True:
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')),sep="\t",header=None)
        df.rename(columns={0:"chr",1:"gene",2:"site",3:"strand"},inplace=True)

        
    elif 'sgr' in filename:
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')),sep="\t",header=None)
        df.rename(columns={0:"chr",1:"site",2:"reads"},inplace=True)
    else:
        False

    return df


######Callbacks


@app.callback(
    Output("graph", "figure"),
    Output("Stored_df", "data"),
    Input("update_button", "n_clicks"),
    State("upload-data", "contents"),
    State("upload-data", "filename"),
    State('upload-data', 'last_modified'),
    State("upload-sites", "contents"),
    State("upload-sites", "filename")
)

def update_output(n_clicks, sgr_contents, sgr_filenames, dates, site_contents, site_filename):


    fig = px.line()
    json_df = {}
    
    if sgr_filenames != None and site_contents != None:
        site_input = parse_contents(site_contents, site_filename,site=True)
        all_normalised_together =pd.DataFrame()
        #open site file rounded to the nearest multiple of 10 (rounding method chosen here)
        site_input.loc[:,'site'] = site_input.loc[:,'site'].apply(lambda x: (x+5)/10).apply(math.floor).apply(lambda x: x*10)   #Preferable 5 up method as not affected by floats

        print(f'''The site file {site_filename} is being used
        Contains: {(site_input.loc[:,'strand'] == 'F').sum()} Forward strands and {(site_input.loc[:,'strand'] == 'R').sum()} Reverse strands ''')

        
        
        
        for i in range(len(sgr_contents)):
            sgr_input = parse_contents(sgr_contents[i], sgr_filenames[i])
            print (f'-----------------------------   \nCurrently working with {sgr_filenames[i]} ')
    
            #Forward and reverse strands made into opposite index arrays (121 is the 0 value)
            #columns are specific genes, rows are reads at a particular distance from the site of that gene 
            #First put into a list of Series as list.append is much more effiecent than pd.concat
            collection_F = []
            collection_R = []  
            
            #Fail counter for determining the strand direction (10 or more should break out of the loop for the sgr_file)
            fails = 0
    
            print (f'''Contains {sgr_input.chr.count()} bin values
Contains {len(sgr_input.loc[:,'chr'].unique())} chromosomes ''')

            #Make a hash table (dict) of each chr slice from the sgr's
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
                    print('Encountered strand direction that is not F or R')
                    fails +=1
                    if fails >= 10:
                        break

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
            after_sum_normalised.name=sgr_filenames[i]

            print(f'The total amount of reads are {total_reads}\nThe normalisation number is {normalisation}')
            
            all_normalised_together = pd.concat([all_normalised_together,after_sum_normalised],axis=1)
            
        print('Finished processing')
        all_normalised_together.insert(0,"Distance",range(-1200,1210,10))
            
        
        for i in all_normalised_together.columns:
            if i == "Distance":
                continue
            
            # print(i)
            # print(all_normalised_together[i])
            
            trace = go.Scatter(
                x=all_normalised_together["Distance"],
                y=all_normalised_together[i],
                mode="lines",
                name= i
                )
                
            fig.add_trace(trace)
            
        json_df = all_normalised_together.to_json(date_format='iso', orient='split')


            
    fig.update_xaxes(title="Position from Site")
    fig.update_yaxes(title="Normalised value")


    return fig, json_df

@app.callback(
    Output("SGR_file_text", "children"),
    Output("Site_file_text", "children"),
    Output("update_button", "disabled"),
    Output("update_button", "color"),
    Input ("upload-data", "filename"),
    Input ("upload-sites", "filename"),
    State("upload-data", "contents"),
    State("upload-sites", "contents"),

)

def update_SGR_filenames(sgr_filenames, site_filename, sgr_contents, site_contents):

    #Default parameters 
    button_off = False
    button_color = "secondary"
    sgr_file_string = "No files currently loaded"
    site_file_string = "No file currently loaded"

    
    #Iterate over sgr_files and determine if they are validish
    if sgr_filenames != None:
        sgr_file_string=f"There are {len(sgr_filenames)} files being used: \n"

        for i in range(len(sgr_contents)):
            try:
                current_file = parse_contents(sgr_contents[i], sgr_filenames[i])
                current_file.rename(columns={0:"chr",1:"site",2:"reads"},inplace=True)
                
                current_file_length = len(current_file.columns)
                
                if current_file_length != 3:
                    sgr_file_string = sgr_file_string + f"The file {sgr_filenames[i]} has {current_file_length} columns when it should have 3 \n"
                    button_off = True
                else:
                    sgr_file_string = sgr_file_string + f"{sgr_filenames[i]} \n"
        
            except:
                sgr_file_string = sgr_file_string + f"The file {sgr_filenames[i]} cannot be loaded (wrong extention?) \n"
                button_off=True
                
    #Determine if the site file is valid
        
    if site_filename != None:
        try:
            site_file_df = parse_contents(site_contents, site_filename,site=True)
            
            site_file_length= len(site_file_df.columns)
            
            if site_file_length != 4:
                site_file_string = f"The site file has {site_file_length} columns when it should have 4"
            else:
                site_file_string = f"The site file loaded is: \n{site_filename}"
            
            
    
        except:
            site_file_string = f"The file {site_filename} could not be loaded"
            button_off = True
          
    if site_filename == None or sgr_filenames == None:
        button_off = True

          
    if button_off == True:
        button_color = "danger"
                
            
    return sgr_file_string, site_file_string, button_off, button_color



@app.callback(
Output( "download_df", "data"),
Input ("download_button", "n_clicks"),
State("Stored_df", "data")
)

def download_df(n_clicks, data):

    if data == None or data == {}:
        df = pd.DataFrame([[1,3],[2,4]])
        raise PreventUpdate
    else:
        df = pd.read_json(data, orient='split')
    
    return dcc.send_data_frame(df.to_csv, "mydf.csv")

   
# @app.callback(
    # Output("Site_file_text", "children"),
    # Input ("upload-sites", "filename")
# )

# def update_Site_filenames(filename):
   # #Update the filename shown
   # # names string
    # # for file in enumerate(filename):
        # # names
    # file_name = "No files currently loaded"
    

    
    # if filename != None:
        
        # return f"The file loaded is {filename}" 
    # return file_name




if __name__ == '__main__':
    app.run_server(debug=True)