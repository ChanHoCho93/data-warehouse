import configparser

# CONFIG
config = configparser.ConfigParser()
config.read('dwh.cfg')

# DROP TABLES
staging_events_table_drop = "DROP TABLE IF EXISTS staging_events";
staging_songs_table_drop = "DROP TABLE IF EXISTS staging_songs";
songplay_table_drop = "DROP TABLE IF EXISTS songplays";
user_table_drop = "DROP TABLE IF EXISTS users";
song_table_drop = "DROP TABLE IF EXISTS songs";
artist_table_drop = "DROP TABLE IF EXISTS artists";
time_table_drop = "DROP TABLE IF EXISTS times";

# CREATE TABLES
staging_events_table_create= ("""CREATE TABLE IF NOT EXISTS staging_events (
artist text, auth text, firstName text, gender text, ItemInSession int,
lastName text, length float8, level text, location text, method text,
page text, registration text, sessionId int, song text, status int,
ts timestamp, userAgent text, userId int)
""")

staging_songs_table_create = ("""CREATE TABLE IF NOT EXISTS staging_songs (
song_id text PRIMARY KEY, artist_id text, artist_latitude float,
artist_longitude float, artist_location text, artist_name text,
duration float, num_songs int, title text, year int)
""")

songplay_table_create = ("""CREATE TABLE IF NOT EXISTS songplays(
songplay_id integer IDENTITY(0,1), start_time timestamp, user_id int NOT NULL, level text, song_id text,
artist_id text, session_id int NOT NULL, location text, user_agent text)
""")

user_table_create = ("""CREATE TABLE IF NOT EXISTS users(
user_id int PRIMARY KEY NOT NULL, first_name text, last_name text, gender text, level text)
""")

song_table_create = ("""CREATE TABLE IF NOT EXISTS songs(
song_id text PRIMARY KEY NOT NULL, title text, artist_id text, year int, duration float)
""")

artist_table_create = ("""CREATE TABLE IF NOT EXISTS artists(
artist_id text PRIMARY KEY NOT NULL, name text, location text, lattitude float, longitude float)
""")

time_table_create = ("""CREATE TABLE IF NOT EXISTS times(
start_time timestamp, hour int, day int, week int, month int, year int, weekday int)
""")

# STAGING TABLES
staging_events_copy = ("""copy staging_events 
                            from {} credentials  
                            'aws_iam_role={}'   
                            json {}  
                            compupdate off
                            region 'us-west-2' 
                            timeformat as 'epochmillisecs';
                        """).format(config.get("S3","LOG_DATA"), config.get("IAM_ROLE", "ARN"), config.get("S3", "LOG_JSONPATH"))

staging_songs_copy = ("""copy staging_songs from {} credentials \'aws_iam_role={}\' JSON 'auto' truncatecolumns compupdate off region \'us-west-2\';
                    """).format(config.get("S3","SONG_DATA"), config.get("IAM_ROLE", "ARN"))

# FINAL TABLES
songplay_table_insert = ("""INSERT INTO songplays (start_time, user_id,level,song_id,artist_id,session_id,location,user_agent)
                        SELECT ts, userId, level, song_id, artist_id, sessionId, location, userAgent
                        FROM(SELECT se.ts, se.userId, se.level, sa.song_id, sa.artist_id, se.sessionId, se.location, se.userAgent
                        FROM staging_events se
                        JOIN(SELECT songs.song_id, artists.artist_id, songs.title, artists.name, songs.duration
                        FROM songs
                        JOIN artists
                        ON songs.artist_id = artists.artist_id) AS sa
                        ON(sa.title = se.song AND sa.name = se.artist AND sa.duration = se.length)
                        WHERE se.page = 'NextSong')
                        """)


user_table_insert = ("""INSERT INTO users (user_id, first_name, last_name, gender, level)
                        SELECT DISTINCT userId, firstName, lastName, gender, level
                        FROM staging_events
                        WHERE page = 'NextSong'
                        """)

song_table_insert = ("""INSERT INTO songs (song_id, title, artist_id, year, duration)
                        SELECT DISTINCT song_id, title, artist_id, year, duration
                        FROM staging_songs
                        WHERE song_id NOT IN (SELECT DISTINCT song_id FROM songs)
                        """)

artist_table_insert = ("""INSERT INTO artists (artist_id, name, location, lattitude, longitude)
                          SELECT DISTINCT artist_id, artist_name, artist_location, artist_latitude, artist_longitude
                          FROM staging_songs
                          WHERE artist_id NOT IN (SELECT DISTINCT artist_id FROM artists)
                          """)

time_table_insert = ("""INSERT INTO times(start_time, hour, day, week, month, year, weekday)
                        SELECT DISTINCT ts, 
                        EXTRACT(HOUR FROM ts), 
                        EXTRACT(DAY FROM ts), 
                        EXTRACT(WEEK FROM ts),
                        EXTRACT(MONTH FROM ts),       
                        EXTRACT(YEAR FROM ts),
                        EXTRACT(DOW FROM ts)
                        FROM staging_events;
                        """)

# QUERY LISTS
create_table_queries = [staging_events_table_create, staging_songs_table_create, songplay_table_create, user_table_create, song_table_create, artist_table_create, time_table_create]
drop_table_queries = [staging_events_table_drop, staging_songs_table_drop, songplay_table_drop, user_table_drop, song_table_drop, artist_table_drop, time_table_drop]
copy_table_queries = [staging_events_copy, staging_songs_copy]
insert_table_queries = [user_table_insert, song_table_insert, artist_table_insert, time_table_insert, songplay_table_insert]
