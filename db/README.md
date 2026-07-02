1) pull latest code from github
2) cd to db folder
2a) python -m pip install -r requirements.txt
2b) python api.py (run api)
2c) it should run http://127.0.0.1:5000
 
3) pre test
3a) try http://127.0.0.1:5000/api/compliance/profiles-by-licence/HC
should show this
 
[
  {
    "display_name": "Light Rigid Truck (2 Axle, \u22648t GVM)",
    "profile_id": "STANDARD_LR_RIGID"
  },
  {
    "display_name": "Medium Rigid Truck (2 Axle, >8t GVM)",
    "profile_id": "STANDARD_MR_RIGID"
  },
  {
    "display_name": "Heavy Rigid Truck (3+ Axle, >8t GVM)",
    "profile_id": "STANDARD_HR_RIGID"
  },
  {
    "display_name": "Prime Mover + Semitrailer",
    "profile_id": "STANDARD_PM_SEMI"
  }
]
 
4) cd to FrontendVue folder
4a) npm install
4b) npm run dev
 
5) test vehicle tab
6) test routing feature
7) optional test login, sign up and configure profile feature
