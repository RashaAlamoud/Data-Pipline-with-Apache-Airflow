import configparser


# CONFIG
config = configparser.ConfigParser()
config.read('dwh.cfg')

# DROP TABLES

staging_events_table_drop = "DROP TABLE IF EXISTS staging_events;"
staging_songs_table_drop = "DROP TABLE IF EXISTS staging_songs;"
songplay_table_drop = "DROP TABLE IF EXISTS songplays;"
user_table_drop = "DROP TABLE IF EXISTS users;"
song_table_drop = "DROP TABLE IF EXISTS songs;"
artist_table_drop = "DROP TABLE IF EXISTS artists;"
time_table_drop = "DROP TABLE IF EXISTS time;"

# CREATE TABLES 

staging_events_table_create= ("""CREATE TABLE staging_events(event_id VARCHAR PRIMARY KEY,artist VARCHAR,
        auth VARCHAR,
        firstName VARCHAR,
        gender  VARCHAR,
        itemInSession INTEGER,
        lastName VARCHAR,
        length   FLOAT,
        level   VARCHAR,
        location VARCHAR,
        method  VARCHAR,
        page    VARCHAR,
        registration  FLOAT,
        sessionId   INTEGER,
        song      VARCHAR,
        status   INTEGER,
        ts      TIMESTAMP,
        userAgent    VARCHAR,
        userId  INTEGER 
    )
""")

staging_songs_table_create = ("""CREATE TABLE staging_songs(
        num_songs INTEGER,
        artist_id  VARCHAR,
        artist_latitude FLOAT,
        artist_longitude FLOAT,
        artist_location VARCHAR,
        artist_name VARCHAR,
        song_id VARCHAR PRIMARY KEY,
        title   VARCHAR,
        duration FLOAT,
        year INTEGER
    )
""")

songplay_table_create = ("""CREATE TABLE songplays(
        songplay_id INTEGER IDENTITY(0,1)   PRIMARY KEY,
        start_time  TIMESTAMP,
        user_id INTEGER ,
        level    VARCHAR,
        song_id  VARCHAR,
        artist_id   VARCHAR ,
        session_id   INTEGER,
        location VARCHAR,
        user_agent  VARCHAR
    )

""")

user_table_create = (""" CREATE TABLE users(
        user_id  INTEGER PRIMARY KEY,
        first_name VARCHAR,
        last_name   VARCHAR,
        gender  VARCHAR,
        level   VARCHAR
    )
""")

song_table_create = (""" CREATE TABLE songs(
        song_id VARCHAR PRIMARY KEY,
        title   VARCHAR ,
        artist_id   VARCHAR ,
        year    INTEGER ,
        duration FLOAT
    )
""")

artist_table_create = ("""CREATE TABLE artists(
        artist_id  VARCHAR  PRIMARY KEY,
        name     VARCHAR ,
        location VARCHAR,
        latitude FLOAT,
        longitude  FLOAT
    )
""")

time_table_create = ("""CREATE TABLE time(
        start_time TIMESTAMP NOT NULL PRIMARY KEY,
        hour INTEGER NOT NULL,
        day INTEGER NOT NULL,
        week INTEGER NOT NULL,
        month INTEGER NOT NULL,
        year INTEGER NOT NULL,
        weekday VARCHAR(20)  NOT NULL
    )
""")

# STAGING TABLES

staging_events_copy = ("""copy staging_events from '{}'
 credentials 'aws_iam_role={}'
 region 'us-west-2' 
 COMPUPDATE OFF STATUPDATE OFF
 JSON '{}'""").format(config.get('S3','LOG_DATA'),
                        config.get('IAM_ROLE', 'ARN'),
                        config.get('S3','LOG_JSONPATH'))

staging_songs_copy = ("""copy staging_songs from '{}'
    credentials 'aws_iam_role={}'
    region 'us-west-2' 
    COMPUPDATE OFF STATUPDATE OFF
    JSON 'auto'
    """).format(config.get('S3','SONG_DATA'), 
                config.get('IAM_ROLE', 'ARN'))


# FINAL TABLES

songplay_table_insert = ("""INSERT INTO songplays (songplay_id,start_time, user_id, level, song_id, artist_id, session_id, location, user_agent) 
    SELECT DISTINCT 
        TIMESTAMP 'epoch' + ts/1000 *INTERVAL '1 second' as start_time, 
        e.user_id, 
        e.user_level,
        s.song_id,
        s.artist_id,
        e.session_id,
        e.location,
        e.user_agent
    FROM staging_events e, staging_songs s
    WHERE e.page = 'NextSong'
    AND e.song_title = s.title
    AND user_id NOT IN (SELECT DISTINCT s.user_id FROM songplays s WHERE s.user_id = user_id
                       AND s.start_time = start_time AND s.session_id = session_id )
""")

user_table_insert = ("""INSERT INTO users (user_id, first_name, last_name, gender, level)  
    SELECT DISTINCT 
        user_id,
        first_name,
       last_name,
        gender, 
        level
    FROM staging_events
    WHERE page = 'NextSong'
    AND user_id NOT IN (SELECT DISTINCT user_id FROM users)

""")
 

song_table_insert = ("""INSERT INTO songs (song_id, title, artist_id, year, duration) 
    SELECT DISTINCT 
        song_id, 
        title,
        artist_id,
        year,
        duration
    FROM staging_songs
    WHERE song_id NOT IN (SELECT DISTINCT song_id FROM songs)
""")



artist_table_insert = ("""INSERT INTO artists (artist_id, name, location, latitude, longitude) 
    SELECT DISTINCT 
    artist_id,
       name,
       location,
        latitude,
        longitude
    FROM staging_songs
    WHERE artist_id NOT IN (SELECT DISTINCT artist_id FROM artists)
""")


time_table_insert = ("""INSERT INTO time (start_time, hour, day, week, month, year, weekday)
    SELECT 
        start_time, 
        EXTRACT(hr from start_time) AS hour,
        EXTRACT(d from start_time) AS day,
        EXTRACT(w from start_time) AS week,
        EXTRACT(mon from start_time) AS month,
        EXTRACT(yr from start_time) AS year, 
        EXTRACT(weekday from start_time) AS weekday 
    FROM (
    SELECT DISTINCT  TIMESTAMP 'epoch' + ts/1000 *INTERVAL '1 second' as start_time 
        FROM staging_events s     
    )
    WHERE start_time NOT IN (SELECT DISTINCT start_time FROM time)

""")

# QUERY LISTS

create_table_queries = [staging_events_table_create, staging_songs_table_create, songplay_table_create, user_table_create, song_table_create, artist_table_create, time_table_create]
drop_table_queries = [staging_events_table_drop, staging_songs_table_drop, songplay_table_drop, user_table_drop, song_table_drop, artist_table_drop, time_table_drop]
copy_table_queries = [staging_events_copy, staging_songs_copy]
insert_table_queries = [songplay_table_insert, user_table_insert, song_table_insert, artist_table_insert, time_table_insert]
