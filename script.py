import psycopg2, pandas as pd, numpy as np
import yaml
with open('config.yaml') as f:
    config = yaml.safe_load(f)
    
from IPython.display import display, HTML




pd.options.display.max_columns = 10
pd.options.display.max_rows = 100

region_lookup = pd.read_csv("ref/region_lookup.csv").set_index("location").to_dict()['region']

songs = ['Song from Impa',
 'Song from Malon',
 'Song from Saria',
 'Song from Composers Grave',
 'Song from Ocarina of Time',
 'Song from Windmill',
 'Sheik in Forest',
 'Sheik in Crater',
 'Sheik in Ice Cavern',
 'Sheik at Colossus',
 'Sheik in Kakariko',
 'Sheik at Temple']

stones_medallions = ['Queen Gohma', 'King Dodongo', 'Barinade', 'Phantom Ganon', 'Volvagia', 'Morpha', 'Bongo Bongo', 'Twinrova']

boss_hearts = {'Fire Temple Volvagia Heart':'Volvagia', 
               'Dodongos Cavern King Dodongo Heart':'King Dodongo',
               'Spirit Temple Twinrova Heart':"Twinrova", 
               'Forest Temple Phantom Ganon Heart':"Phantom Ganon",
               'Jabu Jabus Belly Barinade Heart':"Barinade", 
               'Water Temple Morpha Heart':"Morpha",
               'Deku Tree Queen Gohma Heart':"Queen Gohma", 
               'Shadow Temple Bongo Bongo Heart':"Bongo Bongo"}

def create_pandas_table(sql_query):
    # Create a new cursor
    conn = psycopg2.connect(
    host="localhost",
    database=config['db_name'],
    user=config['db_user'],
    password=config['db_pass'])
    
    cur = conn.cursor()
    table = pd.read_sql_query(sql_query, conn)
    # Close the cursor and connection to so the server can allocate
    # bandwidth to other requests
    cur.close()
    conn.close()
    return table

df_source = create_pandas_table("SELECT * FROM public.seeds")
seeds_num = len(df_source['seed'].unique())

def num_seeds(): 
    print("Number of seeds (sample size): %s " % seeds_num)


def b1():
    df_source = create_pandas_table("SELECT * FROM public.barren_regions")
    seeds_num = len(df_source['seed'].unique())

    df = df_source.copy()
    df['count'] = 1
    df['pct'] = 100 / seeds_num
    df_piv = df.pivot_table(index=['location'],values=['count','pct'],aggfunc=np.sum)
    df_piv = df_piv.sort_values(by='count',ascending=False)
    # print("\nBarren regions:\nThis is NOT the gossip hint system, this is given per the spoiler. The hints are picked from barren regions from this list.\nRead 'count' column as number of seeds that have X region as a barren region.\nNotice how songs areas are never barren. Same goes for barren hints. It appears the randomization engine avoids dealing with this song problem entirely by avoiding hints at those regions altogether.")
    # display(HTML(df_piv.to_html()))
    display(HTML(df_piv.to_html()))









def b2():

    # All woth locations
    df_source = create_pandas_table("SELECT * FROM public.woth_locations")
    seeds_num = len(df_source['seed'].unique())

    df = df_source.copy()
    df['region'] = df['location'].apply(lambda x: region_lookup[x] if x in region_lookup.keys() else "NULL")
    df['overall'] = 100 / seeds_num
    
    df_piv1 = df.pivot_table(index=['seed','region'],values='overall')
    df_piv1['overall'] = 100 / seeds_num
    
    df_piv = df_piv1.pivot_table(index=['region'],values='overall',aggfunc=np.sum)
    df_piv = df_piv.sort_values(by='overall',ascending=False)
    for col in df_piv.columns:
        df_piv[col] = df_piv[col].apply(lambda x: round(x,2))
    # print("\nAll way of the hero locations (by percentage):\nThese are NOT for hints- this is what is fully WOTH for the seed per the log.\nRead this as X% of seeds have this region as WOTH.")
    display(HTML(df_piv.to_html()))
        
        
    

def b2_1():
        # Woth locations without songs
    df_source = create_pandas_table("SELECT * FROM public.woth_locations")
    df = df_source.copy()
    def apply_song(location):
        if location in songs:
            return "song"
        else:
            return "non-song"
    
    # df = df[~df['location'].isin(songs)]
    df['song_status'] = df['location'].apply(apply_song)
    df['region'] = df['location'].apply(lambda x: region_lookup[x] if x in region_lookup.keys() else "NULL")
    
    df['pct'] = 100 / seeds_num
    
    df_piv1 = df.pivot_table(index=['seed','region'],columns=['song_status'],values='pct')
    df_piv1['pct'] = 100 / seeds_num
    df_piv1 = df_piv1.fillna(0)
    
    df_woth = df_piv1.pivot_table(index=['region'],values=['song','non-song','pct'],aggfunc=np.sum)[['song','non-song','pct']]
    
    df_woth = df_woth.sort_values(by='pct',ascending=False)
    for col in df_woth.columns:
        df_woth[col] = df_woth[col].apply(lambda x: round(x,2))
    df_woth.columns = ['song','non-song','overall']
   
    # Woth locations only songs

    df_woth2 = df_woth[df_woth['song']>0]
    
    # print("\nWay of the hero with songs vs. non-songs:\nThese are not mutually exclusive, which is why most with song & non-song will add up to more than the pct. This means WOTH often refers to song, non-song, or both in the same seed.\nAnalyze this by looking at a data point's percent and saying 'At this region, this column (song/non-song/overall) has X% of being WOTH'")
    display(HTML(df_woth.to_html()))
    print('\nFiltered below for song areas only:\n')

    # print("\nWay of the hero with song differences (filtered from above table):")
    display(HTML(df_woth2.to_html()))
    
def b3():

    # Woth items
    df_source = create_pandas_table("SELECT * FROM public.woth_locations")
    seeds_num = len(df_source['seed'].unique())
    
    df = df_source.copy()    
    df['count'] = 1
    df_piv = df.pivot_table(index=['seed','hint_item'],values=['count'],aggfunc=np.sum)
    df_piv.reset_index("hint_item",inplace=True)
    def apply_progressive(item, count):
        if "Progressive" in item:
            return "%s (%s)" % (item, count)
        elif item in ['Claim Check','Eyeball Frog','Eyedrops','Prescription']:
            return "Trade Item"
        elif "Bottle" in item:
            return "Bottle"
        else:
            return item
        
    df_piv['hint_item'] = np.vectorize(apply_progressive)(df_piv['hint_item'], df_piv['count'])
    df_piv['count'] = 1
    df_piv['pct'] = 100 / seeds_num
    df_piv = df_piv.pivot_table(index=['hint_item'],values=['count','pct'],aggfunc=np.sum)

    
    # print("Required WOTH items:\nThere are two major caveats here.\n1) This is showing strictly logically required items.\n2) Magic and Bow are shown as the non-Ganondorf required WOTH. Not entirely sure why or how this works in the log.")
    display(HTML(df_piv.to_html()))
    
def b4():
    # Woth locations
    df_source = create_pandas_table("SELECT * FROM public.woth_locations")
    seeds_num = len(df_source['seed'].unique())
    
    df = df_source.copy()    
    df['count'] = 1
    df_piv = df.pivot_table(index=['seed','location'],values=['count'],aggfunc=np.sum)
    df_piv['count'] = 1
    df_piv['pct'] = 100 / seeds_num
    df_piv.reset_index("location",inplace=True)

    df_piv2 = df_piv.pivot_table(index=['location'],values=['count','pct'],aggfunc=np.sum)
    df_piv2 = df_piv2.sort_values(by='count',ascending=False)
    # print("\nRequired WOTH locations:\nGiven there's so many possible outcomes with ZOOTR, this chart is mostly cosmetic. Regions are better to analyze, except for some logically restricted checks.")
    display(HTML(df_piv2.to_html()))   
    
    
    print("\nSubset for Skulltula House rewards:")
    df_piv2 = df_piv2[df_piv2.index.str.contains("Skulltula Reward")]
    display(HTML(df_piv2.to_html()))   
    

def b5():    
    
    # Skulltula
    df_source = create_pandas_table("SELECT * FROM public.playthrough")
    df = df_source.copy()    
    df = df[df['location'].str.contains(" GS")]
    df['count'] = 1
    df['pct'] = 100 / seeds_num
    
    df_piv = df.pivot_table(index=['location'],values = ['count','pct'],aggfunc=np.sum)
    df_piv = df_piv.sort_values(by=['count'],ascending=False)
    # print("Skulltula locations 'required' per playthrough log\nThese are 'required' in that the playthrough log chose them. Of course there's usually flexibility, but it may be worthwhile to assess the most frequently chosen ones.\nNicely, all 100 are represented here (which somewhat surprised me).")
    display(HTML(df_piv.to_html()))   
    
    
    
    
    
    
def b6():    
    
    
    
    # Sphere length
    df_source = create_pandas_table("SELECT * FROM public.playthrough")
    df_source['sphere'] = df_source['sphere'].astype(int)
    seeds_num = len(df_source['seed'].unique())
    
    df_piv = df_source.pivot_table(index=['seed'],values = ['sphere'],aggfunc=np.max)
    df_piv['count'] = 1
    df_piv['pct'] = 100 / seeds_num
    df_piv = df_piv.pivot_table(index=['sphere'],values=['pct','count'],aggfunc=np.sum)
    df_piv['pct'] = df_piv['pct'].apply(lambda x: round(x,2))
    # print("Sphere distribution:")
    display(HTML(df_piv.to_html()))
    
    ### Biggest playthrough sphere seed is HB9BMIWSKF but its not good bc Mido in logic
    # G3YP766H2T A little better
    
def b6_1():    
    
    
    
    # Sphere index length
    df_source = create_pandas_table("SELECT * FROM public.playthrough")
    df_source['index'] = df_source['index'].astype(int)
    seeds_num = len(df_source['seed'].unique())
    
    df_piv = df_source.pivot_table(index=['seed'],values = ['index'],aggfunc=np.max)
    df_piv['grouping'] = df_piv['index'].apply(lambda x: "%s0 - %s9" % (round(x/10),round(x/10)))
    df_piv['count'] = 1
    df_piv['pct'] = 100 / seeds_num
    df_piv2 = df_piv.pivot_table(index=['grouping'],values=['pct','count'],aggfunc=np.sum)
    df_piv2['pct'] = df_piv2['pct'].apply(lambda x: round(x,2))
    df_piv2 = df_piv2.iloc[5:].append(df_piv2.iloc[0:5])
    # print("Sphere distribution:")
    display(HTML(df_piv2.to_html()))
    
    ### Biggest playthrough sphere seed is HB9BMIWSKF but its not good bc Mido in logic
    # G3YP766H2T A little better
    
    
def b7():    

    # Barren hints
    df_source = create_pandas_table("SELECT * FROM public.gossip_stones_barren")
    df = df_source.copy()
    df['count'] = 1
    df_piv = df.pivot_table(index=['location','seed'],values='count')    
    df_piv['count'] = 1
    df_piv['pct'] = 50 / seeds_num
    df_piv = df_piv.pivot_table(index=['location'],values=['count','pct'],aggfunc=np.sum)
    df_piv['pct'] = df_piv['pct'].apply(lambda x: round(x,2))
    
    df_piv = df_piv.sort_values(by='count',ascending=False)
    # print("\nDistribution of barren hints (2 per seed)\nMost likely regions being given as barren hint are at the top of this list\nThis is different than barren regions in the seed, this is likelihood of any given barren hint being X region.\nThis is less important, this is just the 2 random barren regions you get as hints. More important is the first barren table, what has fully been decided for the seed. This table is much more likely to suffer from sample size inadequacy.")
    display(HTML(df_piv.to_html()))    

def b8():
    # Woth hints
    df_source = create_pandas_table("SELECT * FROM public.gossip_stones_woth")
    df = df_source.copy()
    df['count'] = 1
    df_piv = df.pivot_table(index=['location','seed'],values='count')    
    df_piv['count'] = 1
    df_piv['pct'] = 25 / seeds_num
    df_piv = df_piv.pivot_table(index=['location'],values=['count','pct'],aggfunc=np.sum)
    df_piv['pct'] = df_piv['pct'].apply(lambda x: round(x,2))
   
    df_piv = df_piv.sort_values(by='count',ascending=False)
    # print("\nDistribution of WOTH hints (4 per seed)\nSame notes as above.")
    display(HTML(df_piv.to_html()))    
    
    
    
    
def b9():    
    # Child Entrances 
    df_source = create_pandas_table("SELECT * FROM public.entrances")
    # print("Distribution of Child entrances\nNothing entirely interesting, appears to be distributed based on number of unique entrances to all accessible areas.\nSome of these are grouped by region, others by individual location. A quirk of the log system")
    df = df_source.copy()
    df = df[df['original_spawn']=='Child']
    df = df.iloc[:,1:]

    df['count'] = 1
    df['pct'] = 100 / seeds_num

    df_piv = df.pivot_table(index=['new_spawn'],aggfunc=np.sum)
    df_piv['pct'] = df_piv['pct'].apply(lambda x: round(x,2))
    df_piv = df_piv.sort_values(by=['count'],ascending=False)
    display(HTML(df_piv.to_html()))    

def b10():
    # Adult Entrances
    df_source = create_pandas_table("SELECT * FROM public.entrances")
    # print("Distribution of Adult entrances\nSee above notes.")
    df = df_source.copy()
    df = df[df['original_spawn']=='Adult']
    df = df.iloc[:,1:]

    df['count'] = 1
    df['pct'] = 100 / seeds_num

    df_piv = df.pivot_table(index=['new_spawn'],aggfunc=np.sum)
    df_piv['pct'] = df_piv['pct'].apply(lambda x: round(x,2))
    df_piv = df_piv.sort_values(by=['count'],ascending=False)
    display(HTML(df_piv.to_html()))    
    
    
def b11():    
    # All dungeons
    df_source = create_pandas_table("SELECT * FROM public.playthrough")
    df = df_source.copy()
    df['dungeons_required'] = df['location'].apply(lambda x: 1 if x in stones_medallions else 0)
    df = df[df['dungeons_required']>0]
    
    df_piv = df.pivot_table(index=['seed'],values=['dungeons_required'],aggfunc=np.sum)
    df_piv['count'] = 1
    df_piv['pct'] = 100 / seeds_num

    
    df_piv2 = df_piv.pivot_table(index=['dungeons_required'],values=['dungeons_required','pct'],aggfunc=np.sum)
    df_piv2['pct'] = df_piv2['pct'].apply(lambda x: round(x,2))
    display(HTML(df_piv2.to_html()))    
    
    
    
    
def b11_2():    
    # All dungeons - with boss hearts
    
    # First check all boss hearts
        
    def switch_location(loc):
        if loc in boss_hearts.keys():
            return boss_hearts[loc]
        else:
            return loc
            
        
    ### EXAMPLE WITH BARINADE  
    #   ZZUJJNAMEV
    sample_seed = 'ZZUJJNAMEV'
    
    df_source = create_pandas_table("SELECT * FROM public.playthrough")
    df = df_source.copy()
    df = df[['location','seed']]
    df['dungeons_required'] = df['location'].apply(lambda x: 1 if x in stones_medallions else 0)
    df['location'] = df['location'].apply(switch_location)
    df = df.pivot_table(index=['seed','location'],values=['dungeons_required'],aggfunc=np.sum)    

    df2 = df_source.copy()
    df2 = df2[['location','reward','seed']]
    df2['hearts_required'] = df2['location'].apply(lambda x: 1 if x in boss_hearts.keys() else 0)
    
    def apply_key_rule(x,y):
        if "key" in x.lower():
            return 0
        else:
            return y
    df2['hearts_required'] = np.vectorize(apply_key_rule)(df2['reward'],df2['hearts_required'])
    
    df2['location'] = df2['location'].apply(switch_location)
    df2 = df2.pivot_table(index=['seed','location'],values=['hearts_required'],aggfunc=np.sum)    

    df3 = df.join(df2)
    def apply_int(x):
        try:
            return int(x)
        except:
            return 0

    df3['hearts_required'] = df3['hearts_required'].apply(apply_int)
    
    def apply_designation(x,y):
        if x == 0 and y == 0:
            return "none"
        elif x == 0 and y == 1:
            return "stone_heart"
        elif x == 1 and y == 0:
            return "blue_warp_only"
        elif x == 1 and y == 1:
            return "heart_and_blue_warp"
        else:
            breakpoint()
    
    def apply_dungeon_score(x,y):
        if x == 1 or y == 1:
            return 1
        else:
            return 0
    
    df3['status'] = np.vectorize(apply_designation)(df3['dungeons_required'],df3['hearts_required'])
    df3 = df3[df3['status']!="none"]
    df3['count'] = 1
    df3['dungeon_score'] = np.vectorize(apply_dungeon_score)(df3['dungeons_required'],df3['hearts_required'])

    
    # simple all dungeons table
    df_piv = df3.pivot_table(index=['seed'],values=['dungeon_score'],aggfunc=np.sum)
    df_piv['count'] = 1
    df_piv['pct'] = 100 / seeds_num
    
    df_piv2 = df_piv.pivot_table(index=['dungeon_score'],values=['count','pct'],aggfunc=np.sum)
    df_piv2['pct'] = df_piv2['pct'].apply(lambda x: round(x,2))
    
    display(HTML(df_piv2.to_html()))    
    
    print("\nBreakout by stone hearts\n")

    
    ## breakout of dungeons & hearts
    df_piv3 = df3.pivot_table(index=['seed'],columns=['status'],values=['count'],aggfunc=np.sum)
    df_piv3.columns = ['blue_warp_only','heart_and_blue_warp','stone_heart']
    for c in ['blue_warp_only','heart_and_blue_warp','stone_heart']:
        df_piv3[c] = df_piv3[c].apply(apply_int)
    df_piv3 = df_piv3.fillna(0)
    df_piv3['blue_warp'] = df_piv3['blue_warp_only'] + df_piv3['heart_and_blue_warp']
    df_piv3 = df_piv3.join(df_piv[['dungeon_score']])
    # df_piv3.columns = ['status_count']
    df_piv3['count'] = 1
    df_piv3['pct'] = 100 / seeds_num
    
    df_piv4 = df_piv3.pivot_table(index=['dungeon_score','blue_warp','stone_heart'],values=['count','pct'],aggfunc=np.sum)
    df_piv4['pct'] = df_piv4['pct'].apply(lambda x: round(x,2))
    
    display(HTML(df_piv4.to_html()))    
    
    
    '''
    Three seeds had 6 dungeons required to beat the seed, but then all 3 other BOSS HEARTS had WOTH items:
        ['BGKHID9PTN', 'I8WQ0S1RUA', 'V6SQQGESQ3']
        Lmao
        
        The first one is REAL good
        
    '''    
    
    
def b12():   
    
    # first let's show density per region
    df_source = create_pandas_table("SELECT * FROM public.locations where seed = 'ZZVTXFLCR7'")
    df = df_source.copy()    
    df['count'] = 1
    df['region'] = df['location'].apply(lambda x: region_lookup[x] if x in region_lookup.keys() else "NULL")
    df = df[~df['location'].isin(stones_medallions)]
    df = df[~df['location'].isin(["Link's Pocket"])]
    
    
    
    df_piv = df.pivot_table(index=['region'],aggfunc=np.sum).sort_values(by='count',ascending=False)
    keys = df[df['item'].str.contains("Small Key")].pivot_table(index=['region'],aggfunc=np.sum)
    df_piv = df_piv.join(keys,lsuffix='l')
    df_piv.columns = ['checks','keys']
    df_piv.fillna(0,inplace=True)
    df_piv['keys'] = df_piv['keys'].astype(int)
    df_piv['effective_checks'] = df_piv['checks'] - df_piv['keys']
    df_piv = df_piv.sort_values(by='effective_checks',ascending=False)
    
    display(HTML(df_piv.to_html()))    

def b13():   
    
    # 
    df_source = create_pandas_table("SELECT * FROM public.locations")
    df = df_source.copy()

    df_source2 = create_pandas_table("SELECT * FROM public.woth_locations")
    df2 = df_source2.copy()

    # Get woth locations
    df3 = df.join(df2.set_index(["seed","location"]),on=['seed','location'])
    df3['woth_item'] = df3['hint_item'].apply(lambda x: "non woth" if x != x else "woth")

    # woth_items = list(create_pandas_table("SELECT distinct(hint_item) FROM public.woth_locations")['hint_item'].unique())

    # df['woth_item'] = df['item'].apply(lambda x: "potential woth" if x in woth_items else "junk")
    df = df3.copy()
    df['region'] = df['location'].apply(lambda x: region_lookup[x] if x in region_lookup.keys() else "NULL")
    df = df[df['region']!="Link's Pocket"]
    df['count'] = 1
    
    df_piv = df.pivot_table(index=['seed','region','woth_item'],values=['count'],aggfunc=np.sum)
    
    df_piv2 = df_piv.pivot_table(index=['region','woth_item'],values=['count'],aggfunc=np.sum).reset_index()
    df_piv2['pct'] = 0
    
    def apply_woth_split(loc, count):
        x = df_piv2[df_piv2['region']==loc]['count'].sum()
        y = round(((count/x) * 100),2)
        return y
    
    df_piv2['pct'] = np.vectorize(apply_woth_split)(df_piv2['region'],df_piv2['count'])
    df_piv2 = df_piv2.pivot_table(index=['region','woth_item'],values=['count','pct'],aggfunc=np.sum)
    
    display(HTML(df_piv2.to_html()))    



def b14_1():   
    
    # Woth locations
    df_source = create_pandas_table("SELECT * FROM public.woth_locations")
    seeds_num = len(df_source['seed'].unique())
    
    df = df_source.copy()    
    df['region'] = df['location'].apply(lambda x: region_lookup[x] if x in region_lookup.keys() else "NULL")
    df = df[df['region']=='Deku Tree']
    df['count'] = 1

    df_piv = df.pivot_table(index=['seed','location'],values=['count'],aggfunc=np.sum)
    df_piv['count'] = 1
    df_piv['pct'] = 100 / seeds_num
    df_piv.reset_index("location",inplace=True)

    df_piv2 = df_piv.pivot_table(index=['location'],values=['count','pct'],aggfunc=np.sum)
    df_piv2 = df_piv2.sort_values(by='count',ascending=False)
    # print("\nRequired WOTH locations:\nGiven there's so many possible outcomes with ZOOTR, this chart is mostly cosmetic. Regions are better to analyze, except for some logically restricted checks.")
    display(HTML(df_piv2.to_html()))   


def b14_2():   
    
    # Woth locations
    df_source = create_pandas_table("SELECT * FROM public.woth_locations")
    seeds_num = len(df_source['seed'].unique())
    
    df = df_source.copy()    
    df['region'] = df['location'].apply(lambda x: region_lookup[x] if x in region_lookup.keys() else "NULL")
    df = df[df['region']=='Water Temple']
    df['count'] = 1

    df_piv = df.pivot_table(index=['seed','location'],values=['count'],aggfunc=np.sum)
    df_piv['count'] = 1
    df_piv['pct'] = 100 / seeds_num
    df_piv.reset_index("location",inplace=True)

    df_piv2 = df_piv.pivot_table(index=['location'],values=['count','pct'],aggfunc=np.sum)
    df_piv2 = df_piv2.sort_values(by='count',ascending=False)
    # print("\nRequired WOTH locations:\nGiven there's so many possible outcomes with ZOOTR, this chart is mostly cosmetic. Regions are better to analyze, except for some logically restricted checks.")
    display(HTML(df_piv2.to_html()))   
    
def b14_3():   
    
    # Woth locations
    df_source = create_pandas_table("SELECT * FROM public.woth_locations")
    seeds_num = len(df_source['seed'].unique())
    
    df = df_source.copy()    
    df['region'] = df['location'].apply(lambda x: region_lookup[x] if x in region_lookup.keys() else "NULL")
    df = df[df['region']=='Shadow Temple']
    df['count'] = 1

    df_piv = df.pivot_table(index=['seed','location'],values=['count'],aggfunc=np.sum)
    df_piv['count'] = 1
    df_piv['pct'] = 100 / seeds_num
    df_piv.reset_index("location",inplace=True)

    df_piv2 = df_piv.pivot_table(index=['location'],values=['count','pct'],aggfunc=np.sum)
    df_piv2 = df_piv2.sort_values(by='count',ascending=False)
    # print("\nRequired WOTH locations:\nGiven there's so many possible outcomes with ZOOTR, this chart is mostly cosmetic. Regions are better to analyze, except for some logically restricted checks.")
    display(HTML(df_piv2.to_html()))   













# def unused():


    ### This is already achieved above for breakout of WOTH songs vs. non-songs
    # Luckily the data being pulled two different ways yielded the same thing
    
    # Woth regions
    # df = df_source.copy()    
    # df['count'] = 1
    # df_piv = df.pivot_table(index=['seed','location'],values=['count'],aggfunc=np.sum)
    # df_piv['count'] = 1
    # df_piv.reset_index("location",inplace=True)
    # df_piv['region'] = df_piv['location'].apply(lambda x: region_lookup[x] if x in region_lookup.keys() else "NULL")
    
    # df_piv = df_piv.pivot_table(index=['seed','region'],values=['count'],aggfunc=np.sum)
    # df_piv['count'] = 1
    # df_piv['pct'] = 100 / seeds_num
    
    # df_piv2 = df_piv.pivot_table(index=['region'],values=['count','pct'],aggfunc=np.sum)
    # print("\nRequired WOTH regions:\nThis is properly de-duplicated, so at least 1 WOTH location yields the region required for the seed")
    # display(HTML(df_piv2.to_html()))    

    

    

'''

>>>>>>>>>>>> Revisit logic of "Way of the hero with song differences"
    Can non_songs and songs columns be calc'd as the pieces of all_woth column?


Goal is to have this dataset set up such that future tournaments/events, we can run the exact same analysis and 
    compare differences

two overarching areas for exploration:
    1 - simple data tables
    2 - "are s4 seeds better or worse" - hard to compare to previous settings
    
    starting medallion/stone
    
    Line ~770 in World.py seems to show that songs will never count as "useless" (even Serenade, Prelude)
        therefore any area with a song can never be barren 
    
    This is not supposed to serve as some epic data-oriented approach to changing how people look at seeds.
    It's a simple collection of statistics true to the logs.
    
    While organizing this data I had two concepts at play:
        #1 - Demonstrate data from spoiler logs cleanly
        #2 - Can we answer the question of why season 4 seeds seem worse?
    
    #1 is achieved. #2 is not - it is a difficult question. First, in order to say something is better/worse than
        something else, you'd have to have the baseline of the other thing (in this case, Season 3 or before). 
        Not only that, the comparison of "what" is incredibly subjective. 
        
    I had a few theories or anti-theories on what would constitute "bad" seeds:
        - Forced area revisits: The idea of having to specifically get an item in a first location, go to a second location,
            then revisit the first location with the item retrieved in the second location. Although this is certainly can
            lead to bad seeds, there often are ways to avoid this with logic breaking or even doing things in non-intended
            order (compared to playthrough log)
        - Sphere count: Spheres are interesting, but it's simply the code making any possible playthrough. Further
            (as many experienced players are aware), very tedious logic chains can cause huge sphere counts. For example,
            some Adult temples' key locations will be multiple spheres by themselves. Further, things like Mido's skip
            trivializing WOTH implications for Forest Temple, etc. So sphere count is somewhat interesting but 
            not at all the best indicator of "good" vs. "bad". I'd say they're generally correlated for slightly faster
            seeds having low sphere counts, but inconclusive on the higher sphere counts 
        - 
            
            
    For those reasons and a few other data organization/science reasons, I decided not to pursue this deeply. In
        my opinion, if you want to truly get into the data science methods of how and why seeds are "good" or "bad",
        you'd have to first codify the time cost of every location. In other words, creating an extremely dynamic map
        of how long generally required checks are between each other, including things like warping, save & quitting
        (with random locations), Farore's Wind... entirely too much work for any reasonable human being. 
        
    
    
    Whenever looking at data points that seem close, remember that the randomizer
        can create so many possibilites. So looking at likelihood of 1 random occurrence at 1 location or something
        is not very important. But by looking at the macro level of what's happening, one can use intuition
        to investigate deeper. Further, on some charts (such as Entrance starting locations), not very important
        the ranking between choices, but general groups of high/low will be moderately reliable for outcomes. 
    
    
    
    Simply, the following regions present in WOTH locations are not present in Barren, which all have songs:
        Kakariko Village
        Sacred Forest Meadow
        the Graveyard
        Death Mountain Crater
        Lon Lon Ranch
        Desert Colossus
        Hyrule Field
        Ice Cavern
        Temple of Time

    The take-away is "A barren hint is just not going to touch the topic of songs", not much else
    
    
    
    Way of the hero:
        88.47% of seeds have Kakariko as a WOTH area. 
        
        
    
    WOTH Hint: walk through DMC example
        Look at DMC and look at difference of song vs. non song
            27.56% of WOTHs are non-song for DMC
            46.63% of WOTHs are songs for DMC
            
        Meaning that DMC hints are much more likely to be songs 
        (Side note, this table is not additive because of the changing weight of each location when separating the data)
            
        Then look at the WOTH Hint table (4.32%) - if you get happen to get a DMC hint, 4.32% chance,
            then more than likely (46% vs 27%) it's pointing to a song 
    
    
        So the take-away is, look at the "Way of the hero with song differences" and check out where the dropoff is
            Look at SFM! Way, way, way more likely WOTH for song than item 
            Then look at Ice Cavern - you might think with less checks that it would be song heavy WOTH, but probably because of how blocked off it is from other requirements, 
                perhaps its power as a song location for WOTH is diminished compared to items
                
                
                
                
    Required WOTH items:
        Bomb Bag is pretty low. It's interesting, most people would think higher, because it gives access to so many checks
        But it's a bit of a fallacy to think so, it's just having Bomb Bag makes checking areas way more efficient
        
            
'''