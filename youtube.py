from googleapiclient.discovery import build
import pymongo
import psycopg2
import pandas as pd
import streamlit as st

#API Connection

def Api_connect():
    Api_Id="AIzaSyCf9JWh9Kn781-hCrJsazuhKUTLE4SNGGg"
    Api_Service="youtube"
    Api_version="v3"
    youtube = build(Api_Service,Api_version,developerKey=Api_Id)

    return youtube

youtube=Api_connect()

#get Channel Info

def get_channel_info(channel_id):
    request=youtube.channels().list(
                        part="snippet,contentDetails,statistics",
                        id=channel_id

        ) 
    response=request.execute()

    for i in response["items"]:
        data=dict(channel_Name=i["snippet"]['title'],
                channel_Id=i["id"],
                subscribers=i["statistics"]["subscriberCount"],
                views=i["statistics"]["viewCount"],
                Total_Videos=i["statistics"]["videoCount"],
                channel_Description=i["snippet"]["description"],
                playlist_Id=i["contentDetails"]["relatedPlaylists"]["uploads"])
        
    return data    
    
# get Video IDS

def get_video_ids(Channel_id):
    Video_ids=[]
    request=youtube.channels().list(
                            part="contentDetails",
                            id=Channel_id) 
    response=request.execute()

    Playlist_Id = response['items'][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    next_page_token=None

    while True:
        request=youtube.playlistItems().list(
                                        part="snippet",
                                        playlistId=Playlist_Id,
                                        maxResults=50,
                                        pageToken=next_page_token)

        response1=request.execute()
        next_page_token=response1.get("nextPageToken")

        for i in range (len(response1["items"])):
            Video_ids.append(response1["items"][i]["snippet"]["resourceId"]["videoId"])

        if next_page_token is None:
            break
    return Video_ids

# get video Information

def get_video_info(Video_Ids):
    Video_data=[]
    for video_id in Video_Ids:
        request=youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=video_id
        )
        response=request.execute()

        for item in response["items"]:
            data=dict(channel_Name=item["snippet"]["channelTitle"],
                    channel_Id=item["snippet"]["channelId"],
                    Video_Id=item["id"],
                    Title=item["snippet"]["title"],
                    Tags=item["snippet"].get("tags"),
                    Thumbnails=item["snippet"]["thumbnails"]["default"]["url"],
                    Description=item["snippet"].get("description"),
                    Published_Date=item["snippet"]["publishedAt"],
                    Duration=item["contentDetails"]["duration"],
                    Views=item["statistics"].get("viewCount"),
                    Likes=item["statistics"].get("likeCount"),
                    Comments=item["statistics"].get("commentCount"),
                    Favourite_Count=item["statistics"]["favoriteCount"],
                    Definition=item["contentDetails"]["definition"],
                    Caption_Status=item["contentDetails"]["caption"]
                    )
            Video_data.append(data)
    return Video_data       

#get_Comment_Information
def get_comment_info(video_ids):
    Comment_data = []
    try:
        for video_id in video_ids:
            request = youtube.commentThreads().list(
                part = "snippet",
                videoId = video_id,
                maxResults=50
            )
            response=request.execute()

            for item in response['items']:
                data=dict(Comment_Id = item['snippet']['topLevelComment']['id'],
                        Video_Id = item["snippet"]['topLevelComment']['snippet']['videoId'],
                        Comment_Text = item["snippet"]['topLevelComment']['snippet']['textDisplay'],
                        Comment_Author = item["snippet"]['topLevelComment']['snippet']['authorDisplayName'],
                        Comment_Published = item["snippet"]['topLevelComment']['snippet']['publishedAt'],)
                
                Comment_data.append(data)

    except:
        pass
    return Comment_data

#get_playlist_Details

def get_playlist_details(channel_id):

        next_page_token = None
        All_Data = []

        while True:
                request = youtube.playlists().list(
                        part = 'snippet,contentDetails',
                        channelId = channel_id,
                        maxResults=50,
                        pageToken=next_page_token 
                )
                response = request.execute()

                for item in response['items']:
                        data = dict(Playlist_Id = item['id'],
                                Title= item['snippet']['title'],
                                Channel_Id = item['snippet']['channelId'],
                                Channel_Name = item['snippet']['channelTitle'],
                                PublishedAt = item['snippet']['publishedAt'],
                                Video_Count = item['contentDetails']['itemCount'])
                        
                        All_Data.append(data)
                
                next_page_token = response.get('nextPageToken') 
                if next_page_token is None:
                        break   
        
        return All_Data

#upload_to_Mongodb

client = pymongo.MongoClient("mongodb+srv://sasirekhamohan18:vaithiyanadhan25@cluster0.ywrko.mongodb.net/")
db=client["youtube_data"]

def channel_details(channel_id):
    ch_details = get_channel_info(channel_id)
    pl_details = get_playlist_details(channel_id)
    vi_ids = get_video_ids(channel_id)
    vi_details = get_video_info(vi_ids)
    com_details = get_comment_info(vi_ids)

    coll1 = db["channel_details"]
    coll1.insert_one({"channel_information":ch_details,"playlist_information":pl_details,"video_information":vi_details,"comment_information":com_details})

    return "upload completed successfully"

#Table creations for channels,playlists,videos,comments

def channels_table(channel_name_s):
    mydb=psycopg2.connect(host="localhost",
                        user="postgres",
                        password="12345678",
                        database="youtube_data",
                        port="5432")
    cursor=mydb.cursor()

    create_query = '''create table if not exists channels(channel_Name varchar(100),
                                                    channel_Id varchar(80) primary key,
                                                    subscribers bigint,
                                                    views bigint,
                                                    Total_Videos int,
                                                    channel_Description text,
                                                    playlist_Id varchar(80))'''

    cursor.execute(create_query)
    mydb.commit()


    single_channel_detail=[]
    db=client["youtube_data"]
    coll1=db["channel_details"]
    for ch_data in coll1.find({"channel_information.channel_Name":channel_name_s},{"_id":0}):
        single_channel_detail.append(ch_data["channel_information"])

    df_single_channel_detail=pd.DataFrame(single_channel_detail)

    for index, row in df_single_channel_detail.iterrows():
        insert_query = '''insert into channels(channel_Name,
                                            channel_Id,
                                            subscribers,
                                            views,
                                            Total_Videos,
                                            channel_Description,
                                            playlist_Id)
                                            values(%s, %s, %s, %s, %s, %s, %s)'''
        
        values = (row['channel_Name'],
                row['channel_Id'],
                row['subscribers'],
                row['views'],
                row['Total_Videos'],
                row['channel_Description'],
                row['playlist_Id'])
        
        
        try:

            cursor.execute(insert_query, values)
            mydb.commit()
            
        except:

            news=f"Your Provided channel Name {channel_name_s} is already exists"

            return news 
            
        



def playlist_table(channel_name_s):

    mydb=psycopg2.connect(host="localhost",
                        user="postgres",
                        password="12345678",
                        database="youtube_data",
                        port="5432")
    cursor=mydb.cursor()

    
    create_query = '''create table if not exists playlists (Playlist_Id varchar(100) primary key,
                                                        Title varchar(100),
                                                        Channel_Id varchar(100),
                                                        Channel_Name varchar(100),
                                                        PublishedAt timestamp,
                                                        Video_Count int)'''


    cursor.execute(create_query)
    mydb.commit()

    single_playlist_details=[]
    db=client["youtube_data"]
    coll1=db["channel_details"]
    for ch_data in coll1.find({"channel_information.channel_Name":channel_name_s},{"_id":0}):
         single_playlist_details.append(ch_data["playlist_information"])

    df_single_playlist_details=pd.DataFrame(single_playlist_details[0])

    for index, row in df_single_playlist_details.iterrows():
            insert_query = '''insert into playlists(Playlist_Id,
                                                Title,
                                                Channel_Id,
                                                Channel_Name,
                                                PublishedAt,
                                                Video_Count)
                                                values(%s, %s, %s, %s, %s, %s)'''
            

            
            values = (row['Playlist_Id'],
                    row['Title'],
                    row['Channel_Id'],
                    row['Channel_Name'],
                    row['PublishedAt'],
                    row['Video_Count'])
            
            
            cursor.execute(insert_query, values)
            mydb.commit()



def Videos_table(channel_name_s):
    mydb=psycopg2.connect(host="localhost",
                        user="postgres",
                        password="12345678",
                        database="youtube_data",
                        port="5432")
    cursor=mydb.cursor()

    
    create_query = '''create table if not exists videos (channel_Name varchar(100),
                                                        channel_Id varchar(100),
                                                        Video_Id varchar(30) primary key,
                                                        Title varchar(150),
                                                        Tags text ,
                                                        Thumbnails varchar(200),
                                                        Description text,
                                                        Published_Date timestamp,
                                                        Duration interval,
                                                        Views bigint,
                                                        Likes bigint,
                                                        Comments int,
                                                        Favourite_Count int,
                                                        Definition varchar(10),
                                                        Caption_Status varchar(50))'''


    cursor.execute(create_query)
    mydb.commit()

    single_videos_details=[]
    db=client["youtube_data"]
    coll1=db["channel_details"]
    for ch_data in coll1.find({"channel_information.channel_Name":channel_name_s},{"_id":0}):
        single_videos_details.append(ch_data["video_information"])

    df_single_videos_details=pd.DataFrame(single_videos_details[0])

    for index, row in df_single_videos_details.iterrows():
                insert_query = '''insert into videos(channel_Name,
                                                    channel_Id,
                                                    Video_Id,
                                                    Title,
                                                    Tags,
                                                    Thumbnails,
                                                    Description,
                                                    Published_Date,
                                                    Duration,
                                                    Views,
                                                    Likes,
                                                    Comments,
                                                    Favourite_Count,
                                                    Definition,
                                                    Caption_Status)
                                                    values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''


                
                values = (row['channel_Name'],
                        row['channel_Id'],
                        row['Video_Id'],
                        row['Title'],
                        row['Tags'],
                        row['Thumbnails'],
                        row['Description'],
                        row['Published_Date'],
                        row['Duration'],
                        row['Views'],
                        row['Likes'],
                        row['Comments'],
                        row['Favourite_Count'],
                        row['Definition'],
                        row['Caption_Status'])
                
                
                cursor.execute(insert_query, values)
                mydb.commit()      



def comments_table(channel_name_s):

    mydb=psycopg2.connect(host="localhost",
                        user="postgres",
                        password="12345678",
                        database="youtube_data",
                        port="5432")
    cursor=mydb.cursor()

    drop_table = '''drop table if exists comments'''
    cursor.execute(drop_table)
    mydb.commit()


    create_query = '''create table if not exists comments (Comment_Id varchar(100) primary key,
                                                        Video_Id varchar(50),
                                                        Comment_Text text,
                                                        Comment_Author varchar(150),
                                                        Comment_Published timestamp)'''


    cursor.execute(create_query)
    mydb.commit()

    single_comment_details=[]
    db=client["youtube_data"]
    coll1=db["channel_details"]
    for ch_data in coll1.find({"channel_information.channel_Name":channel_name_s},{"_id":0}):
        single_comment_details.append(ch_data["comment_information"])

    df_single_comment_details=pd.DataFrame(single_comment_details[0])

    for index, row in df_single_comment_details.iterrows():
                insert_query = '''insert into comments(Comment_Id,
                                                    Video_Id,
                                                    Comment_Text,
                                                    Comment_Author,
                                                    Comment_Published)
                                                    values(%s, %s, %s, %s, %s)'''
                

                
                values =(row['Comment_Id'],
                        row['Video_Id'],
                        row['Comment_Text'],
                        row['Comment_Author'],
                        row['Comment_Published'])
                                
                
                cursor.execute(insert_query, values)
                mydb.commit()

      

def tables(single_channel):
    news=channels_table(single_channel)

    if news:
         return news
    
    else:
        playlist_table(single_channel)
        Videos_table(single_channel)
        comments_table(single_channel)

    return "Tables created"



def show_channels_table():
    ch_list = []
    db=client["youtube_data"]
    coll1=db["channel_details"]

    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
        ch_list.append(ch_data["channel_information"])
    df=st.dataframe(ch_list)

    return df


def show_playlists_table():
    pl_list = []
    db=client["youtube_data"]
    coll1=db["channel_details"]

    for pl_data in coll1.find({},{"_id":0,"playlist_information":1}):
        for i in range(len(pl_data["playlist_information"])):
            pl_list.append(pl_data["playlist_information"][i])

    df1=st.dataframe(pl_list)

    return df1


def show_videos_table():
    vi_list = []
    db=client["youtube_data"]
    coll1=db["channel_details"]

    for vi_data in coll1.find({},{"_id":0,"video_information":1}):
        for i in range(len(vi_data["video_information"])):
            vi_list.append(vi_data["video_information"][i])

    df2=st.dataframe(vi_list)

    return df2


def show_comments_table():
    com_list = []
    db=client["youtube_data"]
    coll1=db["channel_details"]

    for com_data in coll1.find({},{"_id":0,"comment_information":1}):
        for i in range(len(com_data["comment_information"])):
            com_list.append(com_data["comment_information"][i])

    df3=st.dataframe(com_list)

    return df3


#streamlit_part

with st.sidebar:
    st.title(":red[YOUTUBE DATA HARVESTING AND WAREHOUSING]")
    st.header("SKILLS takeaway")
    st.caption("Python Scripting")
    st.caption("Data Collection")
    st.caption("MongoDB")
    st.caption("API Intergreation")
    st.caption("Data Management using MongoDB and SQL")

channel_id=st.text_input("Enter Channel Id:")

if st.button("Collect and Store data"):
    ch_ids=[]
    db=client["youtube_data"]
    coll1=db["channel_details"]
    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
        ch_ids.append(ch_data["channel_information"]["channel_Id"])

    if channel_id in ch_ids:
        st.success("Channel Details of given channel id already exists")

    else:
        insert=channel_details(channel_id)
        st.success(insert)

all_channels=[]
db=client["youtube_data"]
coll1=db["channel_details"]

for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
    all_channels.append(ch_data["channel_information"]["channel_Name"])        

unique_channel=st.selectbox("select channel",all_channels)

if st.button("Migrate to SQL"):
    Table=tables(unique_channel)
    st.success(Table)

show_table=st.radio("SELECT THE TABLE FOR VIEW",("CHANNELS","PLAYLISTS","VIDEOS","COMMENTS")) 

if show_table=="CHANNELS":
    show_channels_table()

elif show_table=="PLAYLISTS":
    show_playlists_table()

elif show_table=="VIDEOS":
    show_videos_table()

elif show_table=="COMMENTS":
    show_comments_table()


#SQL CONNECTION

mydb=psycopg2.connect(host="localhost",
                    user="postgres",
                    password="12345678",
                    database="youtube_data",
                    port="5432")
cursor=mydb.cursor()

question =st.selectbox("Select your Question",("1. All the videos and the Channel Name",
                                               "2. Channels with most number of videos",
                                               "3. 10 most viewed videos",
                                               "4. Comments in each videos",
                                               "5. Videos with highest likes",
                                               "6. Likes of all videos",
                                               "7. Views of each channel",
                                               "8. Videos published in the year of 2023",
                                               "9. Average duration of all videos in each channel",
                                               "10.videos with highest number of comments"))


if question == "1. All the videos and the Channel Name":
    query1='''select Title as videos, channel_Name as channelname from videos''' 
    cursor.execute(query1)
    mydb.commit()
    t1=cursor.fetchall()
    df=pd.DataFrame(t1,columns=["video title", "channel name"])
    st.write(df)

elif question == "2. Channels with most number of videos":
    query2='''select channel_Name as channelname, Total_Videos as no_videos from channels
           order by Total_Videos desc''' 
    cursor.execute(query2)
    mydb.commit()
    t2=cursor.fetchall()
    df2=pd.DataFrame(t2,columns=["channel name", "No of Videos"])
    st.write(df2)

elif question == "3. 10 most viewed videos":
    query3='''select Views as views, channel_Name as channelname, Title as videotitle from videos
              where views is not null order by views desc limit 10 ''' 
    cursor.execute(query3)
    mydb.commit()
    t3=cursor.fetchall()
    df3=pd.DataFrame(t3,columns=["views", "channel name", "Video title"])
    st.write(df3)

elif question == "4. Comments in each videos":
       query4='''select Comments as no_comments, Title as videotitle from videos where comments is not null ''' 
       cursor.execute(query4)
       mydb.commit()
       t4=cursor.fetchall()
       df4=pd.DataFrame(t4,columns=["no of comments", "Video title"])
       st.write(df4)

elif question == "5. Videos with highest likes":
       query5='''select Title as videotitle,channel_Name as channelname, likes as likecount
                from videos Where likes is not null order by likes desc ''' 
       cursor.execute(query5)
       mydb.commit()
       t5=cursor.fetchall()
       df5=pd.DataFrame(t5,columns=["Video title", "channel Name","likecount"])
       st.write(df5)

elif question == "6. Likes of all videos":
       query6='''select likes as likecount, Title as videotitle from videos ''' 
       cursor.execute(query6)
       mydb.commit()
       t6=cursor.fetchall()
       df6=pd.DataFrame(t6,columns=["likecount","Video title"])
       st.write(df6)

elif question =="7. Views of each channel":
      query7='''select channel_Name as channelname, views as totalviews from channels'''
      cursor.execute(query7)
      mydb.commit()
      t7=cursor.fetchall()
      df7=pd.DataFrame(t7,columns=["channel Name","Total Views"])
      st.write(df7)

elif question =="8. Videos published in the year of 2023":
      query8='''select Title as videotitle, Published_date as videoreleased, channel_Name as channelname from videos 
                where extract (year from Published_date)=2023 '''
      cursor.execute(query8)
      mydb.commit()
      t8=cursor.fetchall()
      df8=pd.DataFrame(t8, columns=["video title", "Published Date","channel name"])
      st.write(df8)

elif question == "9. Average duration of all videos in each channel":
       query9='''select Channel_Name as channelname, AVG(Duration) as avgergeduration from videos
                     group by channel_name'''
       cursor.execute(query9)
       mydb.commit()
       t9=cursor.fetchall()
       df9=pd.DataFrame(t9,columns=["channel name", "Average Duration"])

       T9=[]
       for index,row in df9.iterrows():
              channel_title=row["channel name"]
              average_Duration=row["Average Duration"]
              average_Duration_str=str(average_Duration)
              T9.append(dict(channeltitle=channel_title, avgduration=average_Duration_str))
       df1=pd.DataFrame(T9)
       st.write(df1)

elif question=="10.videos with highest number of comments":
      query10='''select title as videotitle, channel_name as channelname, comments as comments from videos
                 where comments is not null order by comments desc'''
      cursor.execute(query10)
      mydb.commit()
      t10=cursor.fetchall()
      df10=pd.DataFrame(t10,columns=["Video title","Channel name","comments"])
      st.write(df10)




