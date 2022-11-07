import pyfiglet

# TODO: [x] Make a dooms'DAY' finder 
# TODO: [x] Create Calculations
# TODO: [x] Optimise
# TODO: [x] Can the external prog be used JUST for the cen anchor?
# TODO: [x] MAke a weekday calculator with it


dict_day ={-7 : "Sunday",
           -6 : "Monday",
           -5 : "Tuesday",
           -4 : "Wednesday",
           -3 : "Thursday",
           -2 : "Friday",
           -1 : "Saturday",
           0 : "Sunday",
           1 : "Monday",
           2 : "Tuesday",
           3 : "Wednesday",
           4 : "Thursday",
           5 : "Friday",
           6 : "Saturday" } 

Month_decision = {1 : 3,
                  1.1 : 4, # ? Leap Years
                  2 : 28,
                  2.2 : 29, # ? Leap Years
                  3 : 7,
                  4 : 4,
                  5 : 9,
                  6 : 6,
                  7 : 11,
                  8 : 8,
                  9 : 5,
                  10 : 10,
                  11 : 7,
                  12 : 12}

##!!###############!!##
# !! Input of date !! #
##!!###############!!##
Inputer = str(input('Enter the date in dd/mm/yyyy format: '))
Spliter = Inputer.split('/', 2)

Day = int(Spliter[0])
Month = int(Spliter[1])
Year = int(Spliter[2])

##**###########################**##
# !! DoomsDAY finder functions !! #
##**###########################**##
def get_key(val):
    for key, value in dict_day.items():
         if val == value:
             return key 
    return "key doesn't exist"

def dooms_day(Year):     
    ## gregorian calender repeats every 400 years ##
    k = Year % 400
    ## decide the anchor day ##
    if(0 <= k < 100):
        anchor = 2
    elif(100 <= k < 200):
        anchor = 0
    elif(200 <= k < 300):
        anchor = 5
    else:
        anchor = 3
    y = Year % 100
     
    # dooms day formula by Conway: [y//12] + y mod 12 + ([y mod 12)//4]) mod 7 + anchor
    ## ! Anchor day changes after 100 years and repeats after every 400 years in the following way
    ## 0-99 yrs --> Tuesday
    ## 100-199 yrs --> Sunday
    ## 200-299 yrs --> Friday
    ## 300-399 yr --> Wednesday
    doomsday = ((y//12 + y % 12 + (y % 12)//4)% 7 + anchor) % 7     
    return dict_day[doomsday]


##!!##############!!##
##** Calculations **##
##!!##############!!##

Doom_Day = dooms_day(Year)
print('\n', "Doomsday in the year % s is a % s"%(Year, Doom_Day))

## !! What is the day in anchor for the month?
if (( Year%400 == 0)or (( Year%4 == 0 ) and ( Year%100 != 0))):
    print("%d is a Leap Year, changes made accordingly" %Year)
    if Month == 1:
        Month == 1.1
    elif Month == 2:
        Month == 2.1
else:
    print("%d is Not a Leap Year, no changes made" %Year)

## !! Move from the doomsday to the date in question

LevelMonth = Month_decision[Month]
LevelAnchor = get_key(Doom_Day)

while LevelMonth != Day:
    if Day >= LevelMonth:
        LevelMonth += 1
        LevelAnchor += 1
    elif Day <= LevelMonth:
        LevelMonth -= 1
        LevelAnchor -= 1

while LevelAnchor < 0:
    LevelAnchor += 7
while abs(LevelAnchor) > 6:
    LevelAnchor -= 7
Final = dict_day[LevelAnchor]
print(pyfiglet.print_figlet('{0} is a {1}'.format(Inputer, Final)))
