import json, requests
from picamera import PiCamera
from time import sleep
from PIL import Image, ImageDraw
import cv2
import requests


camera = PiCamera()

url = 'https://app.nanonets.com/api/v2/ObjectDetection/Model/829b3adf-c1e2-4d2d-b985-3e5eb08334ba/LabelFile/'

data = {'file': open('/home/pi/Documents/ParkingSpotDemo/Imgs/ParkingLot.png', 'rb')}

response = requests.post(url, auth=requests.auth.HTTPBasicAuth('PRGd_wwO2IMgFkrTA0CS0q-Ycn5zbQF7', ''), files=data)

boundedBoxPixels = float(0)

response = json.loads(response.text)
im = Image.open("/home/pi/Documents/ParkingSpotDemo/Imgs/ParkingLot.png")
draw = ImageDraw.Draw(im, mode= "RGBA")
prediction = response["result"][0]["prediction"]

# drawing bounding boxes and calculating area of individual rectangles
for i in prediction:
    draw.rectangle((i["xmin"],i["ymin"], i["xmax"], i["ymax"]), fill = (102,255,0,127))
    rectArea = abs(float(i["xmax"] - i["xmin"])) * abs(float(i["ymax"] - i["ymin"]))
    boundedBoxPixels += rectArea

im.save("/home/pi/Documents/ParkingSpotDemo/Imgs/parkingspotannotated.jpg")

# sorting predictions

copyOfPrediction = prediction.copy()

# initializing lists
rows = []
removeCars = []

c = 1
while (len(copyOfPrediction) > 0):
    
    # cars is a list of the cars in a specific row
    cars = []
    cars.append(copyOfPrediction[0])
    

    testYMidCoor = float((copyOfPrediction[0]["ymax"] + copyOfPrediction[0]["ymin"]) / 2)
    
    if c == 1 or c == 2 or c == 4:
        
        upperBounds = testYMidCoor + (0.1 * testYMidCoor)
        lowerBounds = testYMidCoor - (0.1 * testYMidCoor)
    
    else:
        
        upperBounds = testYMidCoor + (0.4 * testYMidCoor)
        lowerBounds = testYMidCoor - (0.4 * testYMidCoor)
        


    for i in range(1,len(copyOfPrediction)):
    
        currYMidCoor = float((copyOfPrediction[i]["ymax"] + copyOfPrediction[i]["ymin"]) / 2)
    
        if (currYMidCoor > lowerBounds and currYMidCoor < upperBounds):
        
            cars.append(copyOfPrediction[i])
            removeCars.append(i)


    # removing current row elements from copyOfPrediction


    for i in range(0,len(removeCars)):
        
        copyOfPrediction.pop(removeCars[i])
        
        # inserting a None element to counteract the shifting of indeces from the pop method
        copyOfPrediction.insert(removeCars[i], None)
    

    #removing first element from copyOfprediction
    copyOfPrediction.pop(0)
    #filter out all the Nones
    copyOfPrediction = list(filter(lambda x: x != None, copyOfPrediction))
    
    #clearing removeCars
    removeCars.clear()
    rows.append(cars)
    
    c += 1
    

#bubble sort the lists
    
size = len(rows)

for i in range(0,size):
    
    for j in range(len(rows[i])-1):
        
        for k in range(0, len(rows[i]) - j - 1):
            
            if (rows[i][k]["xmin"] > rows[i][k+1]["xmin"]):
                
                rows[i][k], rows[i][k+1] = rows[i][k+1], rows[i][k]


# (bLX1, bLY1) is the bottom left corner of the first rectangle
# (tRX1, tRY1) is the top right corner of the first rectangle
# (bLX2, bLY2) is the bottom left corner of the 2nd rectangle
# (tRX2, tRY2) is the top right corner of the 2nd rectangle

def isOverLapping(bLX1, bLY1, tRX1, tRY1, bLX2, bLY2, tRX2, tRY2):
    
   if ((tRY1 > bLY2) or (bLY1 < tRY2)) :
       return False

   if ((tRX1 < bLX2) or (bLX1 > tRX2)) :
       return False

   return True

def calcOverlapArea(bLX1, bLY1, tRX1, tRY1, bLX2, bLY2, tRX2, tRY2):

   areaOfIntersect = (abs(min(tRX1, tRX2) - max(bLX1, bLX2))) * (abs(max(tRY1,tRY2) - min(bLY1, bLY2)))
   return areaOfIntersect

for i in range(0,size):
    
    for j in range(len(rows[i])-1):
        
        # bottom left and top right coordinates for "jth" rectangle
        bLX1 = rows[i][j]["xmin"]
        bLY1 = rows[i][j]["ymax"]
        tRX1 = rows[i][j]["xmax"]
        tRY1 = rows[i][j]["ymin"]
    
        # bottom left and top right coordinates for "j+1th" rectangle
        bLX2 = rows[i][j+1]["xmin"]
        bLY2 = rows[i][j+1]["ymax"]
        tRX2 = rows[i][j+1]["xmax"]
        tRY2 = rows[i][j+1]["ymin"]
        
        # this logic assumes that the predictions list is sorted by location so we are comparing
        # the ith rectangle to its direct neighbor to the right (i+1th)

        if (isOverLapping(bLX1, bLY1, tRX1, tRY1, bLX2, bLY2, tRX2, tRY2)):
        
            totalOverLapArea = calcOverlapArea(bLX1, bLY1, tRX1, tRY1, bLX2, bLY2, tRX2, tRY2)
            boundedBoxPixels -= totalOverLapArea
            
totalPixelArea = float(0)

for i in range(0,size):
    
    length = float(abs(rows[i][0]["xmin"] - rows[i][-1]["xmax"]))
    width = float(abs(rows[i][0]["ymax"] - rows[i][-1]["ymin"]))
                  
    rowArea = length * width
    
    totalPixelArea += rowArea
    
    
indivToTotalRatio = boundedBoxPixels / totalPixelArea

print(indivToTotalRatio)