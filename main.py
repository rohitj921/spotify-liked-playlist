import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import json
import sys
import os
from dotenv import load_dotenv
import base64


load_dotenv(".env")

try:
    # token=json.loads(os.getenv("TOKEN"))
    token=json.loads(base64.b64decode(os.getenv("TOKEN")).decode("utf-8").replace("'", "\""))
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
except Exception as e:
    raise ValueError(f"Missing Environmental Variables.. :{e}")

if None in [token,CLIENT_ID,CLIENT_SECRET]:
    raise ValueError("Missing Environmental Variables..")

scope = "user-library-read playlist-modify-public user-read-email"
redirect_uri = "http://localhost:8888"
sp_oauth = SpotifyOAuth(CLIENT_ID, CLIENT_SECRET, redirect_uri, scope=scope,open_browser=False)

playlist_name = "Liked Public(test)"


    

def auth(sp_oauth: object,token_info=None) -> object:
    """
    Returns Spotify object to make api calls and Refreshed Token after authorization
    
    - sp_oauth = SpotifyOAuth(CLIENT_ID,CLIENT_SECRET,redirect_uri,scope=scope)
    - token_info = Stored access token
    
    """
    refreshed_token=token_info
    try:
        if sp_oauth.is_token_expired(token_info):
            print("refreshing token..")
            refreshed_token = sp_oauth.refresh_access_token(
                token_info["refresh_token"]
            )
            sp = spotipy.Spotify(auth=refreshed_token["access_token"])
        else:
            sp = spotipy.Spotify(auth=token_info["access_token"])
        # making api call to check if everything  is alright
        sp.current_user()

    except Exception as e:
        if "error: invalid_grant, error_description: Invalid refresh token" in str(
            e
        ):
            # seems a new token is generated so refresh token wont't work,
            # creating new token instead

            print("bad token")
            # sp = generate_new_token(sp_oauth)

        elif "The access token expired" in str(e):
            print("elif1")
            refreshed_token = sp_oauth.refresh_access_token(
                token_info["refresh_token"]
            )
            sp = spotipy.Spotify(auth=refreshed_token["access_token"])

        elif "invalid_grant, error_description: Refresh token revoked" in str(e):
            print(
                "Seems you have revoked app authorization, please authorize again!"
            )
            # sp = generate_new_token(sp_oauth)

        else:
            print(e)
            refreshed_token = sp_oauth.refresh_access_token(
                token_info["refresh_token"]
            )
            sp = spotipy.Spotify(auth=refreshed_token["access_token"])
        sys.exit()
        
    if os.path.exists(".cache"):
        os.remove(".cache")
        
    return sp, refreshed_token


# To get all liked songs
def get_liked_playlist(sp: object) -> list:
    """
    Returns track ids of songs within liked songs playlist.
    """
    offset = 0
    track_ids = []
    results = []

    while True:
        res = sp.current_user_saved_tracks(limit=50, offset=offset)
        results.extend(res["items"])

        if len(res["items"]) == 0:
            break
        offset += 50

    for item in results:
        track = item["track"]
        # print(track['id'])
        # print(track)
        # break
        track_ids.append(track["id"])
        # print(track["name"])

    return track_ids


def existing_playlist_name(sp: object, playlist_name: str) -> str:
    """
    checks if playlist name already exists else creates new public playlist and returns playlist id.
    """
    playlist_name = playlist_name.strip()

    playlist = sp.current_user_playlists()
    for p in playlist["items"]:
        # print(p['name'])
        if p["name"] == playlist_name:
            # print("exists")
            position = 0
            return p["id"], position

    playlist = sp.user_playlist_create(user=sp.current_user()["id"], name=playlist_name, public=True, description="This playlist is a collection of all the songs I have liked on Spotify, and is automatically updated whenever I add new songs to my Liked Songs library.")
    # print(playlist,"\n")
    # print(playlist["id"])
    position = None
    return playlist["id"], position


def get_public_playlist(sp: object, playlist_id: str) -> list:
    """
    Takes public playlist id and returns track id's of all existing songs within playlist.
    """
    offset = 0
    track_ids = []
    results = []
    while True:
        res = sp.playlist_items(
            playlist_id=playlist_id, fields="items(track(id))", limit=100, offset=offset
        )

        results.extend(res["items"])
        # print(results)
        if len(res["items"]) == 0:
            break
        offset += 100
    """
    add try except
    """
    # print(results)
    track_ids = [x["track"]["id"] for x in results]
    # print(track_ids)
    # print(len(track_ids))
    return track_ids


def check_tracks_in_playlist(old_track_id: list, track_ids: list) -> list:
    """
    Checks if song already exists in playlist, returns filtered track id's of new songs.

    """
    filtered_track_ids = []
    for id in track_ids:
        if id not in old_track_id:
            filtered_track_ids.append(id)

    # print(len(filtered_track_ids))
    return filtered_track_ids


def add_to_playlist(sp: object, playlist_id: str, track_ids: list, position):
    """
    Adds list of track(id's) to given spotify playlist.
    """
    # if position is 0 songs will be added on top , in bottom if none

    for i in range(0, len(track_ids), 50):
        sp.playlist_add_items(
            playlist_id=playlist_id, items=track_ids[i : i + 50], position=position
        )


def main():
    
    sp,rtoken=auth(sp_oauth,token)

    new_track_ids = get_liked_playlist(sp)

    print(f"\nTotal Liked Songs Found : {len(new_track_ids)}")
    playlist_id, position = existing_playlist_name(sp, playlist_name)

    old_track_ids = get_public_playlist(sp, playlist_id)

    filtered_track_ids = check_tracks_in_playlist(old_track_ids, new_track_ids)

    # print(filtered_track_ids)

    if len(filtered_track_ids) != 0:
        print(f"New Tracks :  {len(filtered_track_ids)} ")
        add_to_playlist(sp, playlist_id, filtered_track_ids, position)
        print(f"Successfully added {len(filtered_track_ids)} songs added to {playlist_name}.")  # {playlist['name']}
        return
    
    print(f"\n{playlist_name} is already up to date.")


if __name__ == "__main__":
    main()

