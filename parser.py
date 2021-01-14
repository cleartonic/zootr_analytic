import pandas as pd, numpy as np, glob, os, sys, json, shutil
from sqlalchemy import create_engine
import yaml
with open('config.yaml') as f:
    config = yaml.safe_load(f)
    
    
pd.options.display.max_columns = 10


OVERRIDE_SEED_CHECK = False
MOVE_FINISHED = True

SEEDS = True
ITEM_POOL = True
ENTRANCES = True
LOCATIONS = True
WOTH_LOCATIONS = True
BARREN_REGIONS = True
GOSSIP_STONES = True
PLAYTHROUGH = True


engine = create_engine(config['db_string'], echo=False)
output_path = os.path.join('git_OoT-Randomizer','Output')
logs = glob.glob(os.path.join(output_path,"*.json"))
keys = [':version',
 'file_hash',
 ':seed',
 ':settings_string',
 ':enable_distribution_file',
 'settings',
 'randomized_settings',
 'starting_items',
 'item_pool',
 'dungeons',
 'trials',
 'entrances',
 'locations',
 ':woth_locations',
 ':barren_regions',
 'gossip_stones',
 ':playthrough',
 ':entrance_playthrough']

if True:
    
    existing_seeds_seeds = engine.execute("SELECT seed FROM seeds").fetchall()
    existing_seeds_seeds = [i[0] for i in existing_seeds_seeds]
    existing_seeds_item_pool = engine.execute("SELECT seed FROM item_pool").fetchall()
    existing_seeds_item_pool = [i[0] for i in existing_seeds_item_pool]
    existing_seeds_entrances = engine.execute("SELECT seed FROM entrances").fetchall()
    existing_seeds_entrances = [i[0] for i in existing_seeds_entrances]
    existing_seeds_locations = engine.execute("SELECT seed FROM locations").fetchall()
    existing_seeds_locations = [i[0] for i in existing_seeds_locations]
    existing_seeds_woth_locations = engine.execute("SELECT seed FROM woth_locations").fetchall()
    existing_seeds_woth_locations = [i[0] for i in existing_seeds_woth_locations]
    existing_seeds_barren_regions = engine.execute("SELECT seed FROM barren_regions").fetchall()
    existing_seeds_barren_regions = [i[0] for i in existing_seeds_barren_regions]
    existing_seeds_gossip_stones = engine.execute("SELECT seed FROM gossip_stones").fetchall()
    existing_seeds_gossip_stones = [i[0] for i in existing_seeds_gossip_stones]
    existing_seeds_playthrough = engine.execute("SELECT seed FROM playthrough").fetchall()
    existing_seeds_playthrough = [i[0] for i in existing_seeds_playthrough]

    while logs:
        with open(logs[0]) as f:
            data = json.load(f)
        
        print("Processing %s" % logs[0])
        seed = data[':seed']
        existing_seeds = engine.execute("SELECT seed FROM seeds").fetchall()
        existing_seeds = [i[0] for i in existing_seeds]
        
        
        filename = os.path.basename(logs[0])
        starting_age = data['randomized_settings']['starting_age']


        # seeds
        if SEEDS:
            
            
            df = pd.DataFrame({'filename' : filename, 'seed': seed, 'starting_age':starting_age},index=[0])
            df.set_index('filename',inplace=True)
            if seed not in existing_seeds_seeds:
                df.to_sql('seeds', con=engine, if_exists='append')
        
        
        # item_pool
        if ITEM_POOL:
            df = pd.DataFrame(data['item_pool'],index=[0]).T
            df.index.name = 'item'
            df.columns = ['count']
            df['seed'] = seed
            if seed not in existing_seeds_item_pool:
                df.to_sql('item_pool', con=engine, if_exists='append')
        
        
        # entrances
        if ENTRANCES:
            master_data = {}
            num = 0
            for k, v in data['entrances'].items():
                temp_data = {}
                if "Adult" in k:
                    e = 'Adult'
                else:
                    e = 'Child'
                temp_data['original_spawn'] = e
                
                if type(v) == str:
                    s = v
                else:
                    s = v['from']
                temp_data['new_spawn'] = s
                master_data[num] = temp_data
                num += 1
            
            df = pd.DataFrame(master_data).T
            df.set_index("original_spawn",inplace=True)
            df['seed'] = seed
            if seed not in existing_seeds_entrances:
                df.to_sql('entrances', con=engine, if_exists='append')
        
        
        # locations
        if LOCATIONS:
            data['locations']['LW Deku Scrub Near Bridge'] = data['locations']['LW Deku Scrub Near Bridge']['item']
            data['locations']['LW Deku Scrub Grotto Front'] = data['locations']['LW Deku Scrub Grotto Front']['item']
            data['locations']['HF Deku Scrub Grotto'] = data['locations']['HF Deku Scrub Grotto']['item']
            df = pd.DataFrame(data['locations'],index=[0]).T
            df.index.name = 'location'
            df.columns = ['item']
            df['seed'] = seed
            if seed not in existing_seeds_locations:
                df.to_sql('locations', con=engine, if_exists='append')
        
        # woth locations
        if WOTH_LOCATIONS:
            for k, v in data[':woth_locations'].items():
                if type(v) == dict:
                    data[':woth_locations'][k] = v['item']
            df = pd.DataFrame(data[':woth_locations'],index=[0]).T
            df.index.name = 'location'
            df.columns = ['hint_item']
            df['seed'] = seed
            
            if seed not in existing_seeds_woth_locations:
                df.to_sql('woth_locations', con=engine, if_exists='append')
            
            
        # barren_regions
        if BARREN_REGIONS:
            df = pd.DataFrame(data[':barren_regions'])
            df['seed'] = seed
            df.set_index(0,inplace=True)
            df.index.name = 'location'
            df.columns = ['seed']
            if seed not in existing_seeds_barren_regions:
                df.to_sql('barren_regions', con=engine, if_exists='append')
            
        
            
        if GOSSIP_STONES:
            # gossip_stones
            master_dict = {}
            
            num = 0
            for k, v in  data['gossip_stones'].items():
                d = {}
                d['gossip_stone'] = k
                t = v['text']
                d['text'] = t
                
                if "#" in t and "randomizer" not in t.lower():
                    if "foolish" in t:
                        r = t.split("#")[1]
                        h = None
                        tp = 'barren'
                    elif "way of the hero" in t:
                        r = t.split("#")[1]
                        h = None
                        tp = 'woth'
                    elif "teaches" in t or "melody" in t or "Composer's" in t or "echoes" in t:
                        # breakpoint()
                        r = t.split("#")[1]
                        h = t.split("#")[3]
                        tp = 'song' 
                    else:
                        if len(t) - len(t.replace("#","")) == 4:
                            r = t.split("#")[1]
                            h = t.split("#")[3]
                            tp = 'standard'                
                        else:
                            print("Hint error %s" % t)
                            continue                
            
                else:
                    continue
                
                d['location'] = r
                d['reward'] = h
                d['type'] = tp
                
                
                master_dict[num] = d
                num += 1
            
            df = pd.DataFrame(master_dict).T
            df['seed'] = seed
            df.set_index('gossip_stone',inplace=True)
            
            # the below assumes if the seed is not in gossip_stones specifically, it's not in all of the gossip_stones
            if seed not in existing_seeds_gossip_stones:
                df.to_sql('gossip_stones', con=engine, if_exists='append')
        
                df2 = df[df['type']=='woth']
                df2.drop('reward',axis=1,inplace=True)
                df2.to_sql('gossip_stones_woth', con=engine, if_exists='append')
                
                df2 = df[df['type']=='barren']
                df2.drop('reward',axis=1,inplace=True)
                df2.to_sql('gossip_stones_barren', con=engine, if_exists='append')
                
                df2 = df[df['type']=='song']
                df2.to_sql('gossip_stones_songs', con=engine, if_exists='append')
            
                df2 = df[df['type']=='standard']
                df2.to_sql('gossip_stones_standard', con=engine, if_exists='append')
                
                df2 = df[(df['type']=='standard') | (df['type']=='song')]
                df2.to_sql('gossip_stones_standard_songs', con=engine, if_exists='append')
        
    
            # print(df)
        
        # playthrough
        if PLAYTHROUGH:
            master_data = {}
            num = 0
            for k, v in data[':playthrough'].items():
                for k2, v2 in v.items():
                    master_data[num] = {'sphere':k, 
                                        'location':k2,
                                        'reward':v2}
                    num += 1
            df = pd.DataFrame(master_data).T
            df['seed'] = seed
            if seed not in existing_seeds_playthrough:
                df.to_sql('playthrough', con=engine, if_exists='append')
        
    
    
    
        
        
        if MOVE_FINISHED:
            shutil.move(logs[0],os.path.join(os.path.dirname(logs[0]),'finished',os.path.basename(logs[0])))
        logs = glob.glob(os.path.join(output_path,"*.json"))
    
    
    
    
def move_files_up():
    logs = glob.glob(os.path.join(output_path,'finished',"*.json"))
    for l in logs:
        print("Moving %s" % l)
        shutil.move(l,os.path.join(os.path.dirname(l),os.path.pardir,os.path.basename(l)))

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
'''
truncate barren_regions;
truncate entrances;
truncate item_pool;
truncate locations;
truncate playthrough;
truncate seeds;
truncate woth_locations;
truncate gossip_stones;
truncate gossip_stones_barren;
truncate gossip_stones_songs;
truncate gossip_stones_standard;
truncate gossip_stones_standard_songs;
truncate gossip_stones_woth;


'''    
    
    
    
    
    
'''
select * from  barren_regions;
select * from  entrances;
select * from  item_pool;
select * from  locations;
select * from  playthrough;
select * from  seeds;
select * from  woth_locations;
select * from  gossip_stones;
select * from  gossip_stones_barren;
select * from  gossip_stones_songs;
select * from  gossip_stones_standard;
select * from  gossip_stones_standard_songs;
select * from  gossip_stones_woth;
'''

