import requests
import json
import os
from decimal import Decimal
import schedule
import time
from datetime import datetime, timedelta
from urllib3.exceptions import MaxRetryError
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

Cookies = ""
merged_data = []
date_format = "%Y-%m-%dT%H:%M:%S"
login_url = "https://www.data.brisbane.qld.gov.au/data/data/login_generic?came_from=/data/user/logged_in"
intersections_url = "https://www.data.brisbane.qld.gov.au/data/dataset/56e19d91-d571-4b45-bfdf-f0f00aeb2343/resource/651f7be1-c183-48b5-96a8-fe372e91adab/download/traffic-data-at-int.json"

gauth = GoogleAuth()
gauth.LocalWebserverAuth() 
drive = GoogleDrive(gauth)
folder = "1AlPHEKv8QAjmDxRp0Q7AwSnr8J7w5feJ"
file_path = "/Users/priyagunda/Documents/Traffic Congestion Visual Analytics/traffic_intersections_data.json"
file_name = os.path.basename(file_path)
       

with open("Backups/locations.json", 'r') as json_file:
    locations = json.load(json_file)

# Custom function to serialize datetime objects to ISO 8601 strings
def custom_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()

# Define a custom encoder for Decimal objects
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)  # Convert Decimal to string
        return super(DecimalEncoder, self).default(o)

def get_cookies():
    # user credentials
    payload = {
        "login": "priya",
        "password": "password"
    }
    # fetching auth_token which required to authenticate the user
    req = requests.Session()
    response = req.post(login_url, data=payload)
    if response.status_code != 200:
        return ""
    cookies = '; '.join([f'{name} = {value}' for name, value in req.cookies.items()])
    return cookies


def get_traffic_data(cookies):
    # fetching BCC traffic data at intersections
    headers = {
        "Cookie": cookies,
    }
    try:
        data_res = requests.get(intersections_url, headers=headers)
        if data_res.status_code != 200:
            global Cookies
            Cookies = get_cookies
        return json.loads(data_res.text)
    except MaxRetryError as e:
        time.sleep(50);
    except Exception as e:
        return;

def fetch_and_save():
    global Cookies
    if len(Cookies) == 0:
        Cookies = get_cookies()

    print("\n**** Getting and Saving data, Job started at ", datetime.now())
    # fetch traffic management - intersection api data
    traffic_data = get_traffic_data(Cookies)
    if traffic_data is not None:
        print("Number of recorded inserted: ", len(traffic_data))
        global merged_data
        # create realtional data
        for traffic in traffic_data:
            dsN, mfN, rfN, degree_of_congestion = (0,0,0,"")
            for i in range(1,10):
                if "ds"+str(i) in traffic.keys():
                    if traffic["ds"+str(i)] > dsN:
                        dsN = traffic["ds"+str(i)]
                    if traffic["mf"+str(i)] > mfN:
                        mfN = traffic["mf"+str(i)]
                    if traffic["rf"+str(i)] > rfN:
                        rfN = traffic["rf"+str(i)]
                else:
                    break

            if dsN > 45:
                degree_of_congestion = "high"
            elif dsN < 20:
                degree_of_congestion = "low"
            else:
                degree_of_congestion = "moderate"

            for loc in locations:
                if traffic["tsc"] == loc["tsc"] and traffic["ss"] == loc["subsystem"]:
                    merged_data.append({
                        "dbid": traffic["dbid"],
                        "recorded": datetime.strptime(traffic["recorded"], date_format),
                        "region": loc["region"] if "region" in loc else (loc["suburb"] if "suburb" in loc else ""),
                        "subsystem": loc["subsystem"],
                        "tsc": loc["tsc"],
                        "ct": traffic["ct"],
                        "coordinates": loc["coordinates"] if "coordinates" in loc else "",
                        "degree of saturation" : dsN,
                        "measured flow": mfN,
                        "reconsituted flow": rfN,
                        "degree_of_congestion": degree_of_congestion
                    })
        # get last index for current_recorded_time
        current_recorded_time = merged_data[0]["recorded"] + timedelta(minutes=1)
        json_data = []
        for ind in range(len(merged_data)):
            if merged_data[ind]["recorded"] < current_recorded_time:
                json_data.append(merged_data[ind])
            else:
                break

        print("json len: ", len(json_data))
        print("first: ", json_data[0])
        print("last: ", json_data[len(json_data)-1])

        merged_data = merged_data[ind+1:]
        print("merged len: ", len(merged_data))
        print("first: ", merged_data[0] if len(merged_data) > 0 else 0)
        print("last: ", merged_data[len(merged_data)-1] if len(merged_data) > 0 else 0)

        # save to json file
        with open("traffic_intersections_data.json", "w") as file:
            json.dump(json_data, file, default=custom_serializer)
        print(f"\n Data saved to display_data.json")

        file_list = drive.ListFile({'q': f"'{folder}' in parents and trashed=false"}).GetList()
        for file in file_list:
            if file['title'] == file_name:
                file.SetContentFile(file_path)
                file.Upload()
                print(f"Replaced {file_name} on Google Drive.")
    else:
        return
        

if __name__ == '__main__':
    print("**** main started at ", datetime.now())
    # fetch_and_save()
    # create cron job
    schedule.every(1).minutes.do(fetch_and_save)
    while True:
        schedule.run_pending()
        time.sleep(5)
