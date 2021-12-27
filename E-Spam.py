#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#######################################################################################################
############################################## E-Spammer ##############################################
#######################################################################################################
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
###
### Function: Allows you to scan for spam comments with multiple methods, and delete them all at once
###
### Purpose:  Spam :>
###
### NOTES:    1. This is a work in progress.
###           2. If something doesn't work I'll try to fix it but might not
###              even know how, so don't expect too much.
###
###
### Author:   EnlX - https://Twitter.com/EnlixeID
###
### IMPORTANT:  I OFFER NO WARRANTY OR GUARANTEE FOR THIS SCRIPT. USE AT YOUR OWN RISK.
###             I tested it on my own and implemented some failsafes as best as I could,
###             but there could always be some kind of bug. You should inspect the code yourself.
version = "1.0.0"
configVersion = 2
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

# Standard Libraries
import io
import os
import re
import sys
import time
from datetime import datetime
import traceback
import platform
import pyautogui
import requests
from base64 import b85decode as b64decode
from configparser import ConfigParser
from pkg_resources import parse_version

# Non Standard Modules
from colorama import init, Fore as F, Back as B, Style as S

##########################################################################################
############################## UTILITY FUNCTIONS #########################################
########################################################################################## 

############################### User Choice #################################
# User inputs Y/N for choice, returns True or False
# Takes in message to display

def choice(message="", bypass=False):
  if bypass == True:
    return True

  # While loop until valid input
  valid = False
  while valid == False:
    response = input("\n" + message + f" ({F.LIGHTCYAN_EX}y{S.R}/{F.LIGHTRED_EX}n{S.R}): ")
    if response == "Y" or response == "y":
      return True
    elif response == "N" or response == "n":
      return False
    else:
      print("\nInvalid Input. Enter Y or N")

############################# CONFIG FILE FUNCTIONS ##############################
def create_config_file():
  def config_path(relative_path):
    if hasattr(sys, '_MEIPASS'): # If running as a pyinstaller bundle
        #print("Test1") # For Debugging
        #print(os.path.join(sys._MEIPASS, relative_path)) # For Debugging
        return os.path.join(sys._MEIPASS + "/assets/", relative_path)
    #print("Test2") # for Debugging
    #print(os.path.join(os.path.abspath("assets"), relative_path)) # For debugging
    # return os.path.join(os.path.abspath("assets"), relative_path) # If running as script, specifies resource folder as /assets
    return os.path.join("./assets", relative_path) # If running as script, specifies resource folder as ./assets


  configFileName = "SpamConfig.ini"
  confirm = True
  if os.path.exists(configFileName):
    print(f"{B.RED}{F.WHITE}WARNING!{S.R} {F.YELLOW}SpamConfig.ini{S.R} file already exists. This would overwrite the existing file.")
    confirm = choice("Create new empty config file and overwrite existing?")
    if confirm == True:
      try:
        os.remove(configFileName)
      except:
        traceback.print_exc()
        print("Error Code F-1: Problem deleting existing existing file! Check if it's gone. The info above may help if it's a bug.")
        print("If this keeps happening, you may want to report the issue here: https://github.com/ThioJoe/YouTube-Spammer-Purge/issues")
        input("Press enter to Exit...")
        sys.exit()
    else:
      return None

  if confirm == True:
    # Get default config file contents
    try:
      with open(config_path('default_config.ini'), 'r', encoding="utf-8") as defaultConfigFile:
        data = defaultConfigFile.read()
      defaultConfigFile.close()
    except:
      traceback.print_exc()
      print(f"{B.RED}{F.WHITE}Error Code: F-2{S.R} - Problem reading default config file! The info above may help if it's a bug.")
      input("Press enter to Exit...")
      sys.exit()

    # Create config file
    try:
      configFile = open(configFileName, "w", encoding="utf-8")
      configFile.write(data)
      configFile.close()
    except:
      traceback.print_exc()
      print(f"{B.RED}{F.WHITE}Error Code: F-3{S.R} Problem creating config file! The info above may help if it's a bug.")
      input("Press enter to Exit...")
      sys.exit()

    if os.path.exists(configFileName):
      parser = ConfigParser()
      try:
        parser.read("SpamConfig.ini", encoding="utf-8")
        if parser.get("general", "use_this_config").lower() == "ask":
          print(f"{B.GREEN}{F.BLACK}SUCCESS!{S.R} {F.YELLOW}SpamConfig.ini{S.R} file created successfully.")
          print("\nYou can now edit the file to your liking.\n")
          input("Press enter to Exit...")
          sys.exit()
        else:
          print("Something might have gone wrong. Check if SpamConfig.ini file exists and has text.")
          input("Press enter to Exit...")
          sys.exit()
      except SystemExit:
        sys.exit()
      except:
        traceback.print_exc()
        print("Something went wrong when checking the created file. Check if SpamConfig.ini exists and has text. The info above may help if it's a bug.")
        input("Press enter to Exit...")
        sys.exit()
  else:
    return None

# Put config settings into dictionary
def load_config_file():
  configFileName = "SpamConfig.ini"
  if os.path.exists(configFileName):
    try:
      with open(configFileName, 'r', encoding="utf-8") as configFile:
        configData = configFile.read()
        configFile.close()
    except:
      traceback.print_exc()
      print(f"{B.RED}{F.WHITE}Error Code: F-4{S.R} - Config file found, but there was a problem loading it! The info above may help if it's a bug.")
      print("\nYou can manually delete SpamConfig.ini and use the program to create a new default config.")
      input("Press enter to Exit...")
      sys.exit()
    
    # Sanitize config Data by removing quotes
    configData = configData.replace("\'", "")
    configData = configData.replace("\"", "")

    # Converts string from config file, wraps it to make it behave like file so it can be read by parser
    # Must use .read_file, .read doesn't work
    wrappedConfigData = io.StringIO(configData)
    parser = ConfigParser()
    parser.read_file(wrappedConfigData)
    #configDictRaw = {s:dict(parser.items(s)) for s in parser.sections()}

    # Convert raw config dictionary into easier to use dictionary
    settingsToKeepCase = ["your_channel_id", "video_to_scan", "channel_ids_to_filter", "regex_to_filter", "channel_to_scan"]
    validWordVars = ['ask', 'mine']
    configDict = {}
    for section in parser.sections():
      for setting in parser.items(section):
        # Setting[0] is name of the setting, Setting[1] is the value of the setting
        if setting[0] in settingsToKeepCase and setting[1].lower() not in validWordVars:
          configDict[setting[0]] = setting[1]
        else:
          # Take values out of raw dictionary structure and put into easy dictionary with processed values
          configDict[setting[0]] = setting[1].lower()
          if setting[1].lower() == "false":
            configDict[setting[0]] = False
          elif setting[1].lower() == "true":
            configDict[setting[0]] = True

    return configDict
  else:
    return None
    
############################# Check For Update ##############################
def check_for_update(currentVersion, silentCheck=False):
  isUpdateAvailable = False
  try:
    response = requests.get("https://api.github.com/repos/Enlixe/E-Spam/releases/latest")
    latestVersion = response.json()["name"]
  except Exception as e:
    if silentCheck == False:
      print(e + "\n")
      print(f"{B.RED}{F.WHITE}Error Code U-1:{S.R} Problem checking for update! See above error for more details.\n")
      print("If this keeps happening, you may want to report the issue here: https://github.com/Enlixe/E-Spam/issues")
      input("Press enter to Exit...")
      sys.exit()
    elif silentCheck == True:
      return isUpdateAvailable

  if parse_version(latestVersion) > parse_version(currentVersion):
    isUpdateAvailable = True
    if silentCheck == False:
      print("--------------------------------------------------------------------------------")
      print(f"\nA {F.LIGHTGREEN_EX}new version{S.R} is available!")
      print("  > Current Version: " + currentVersion)
      print("  > Latest Version: " + latestVersion)
      print("\nAvailable Here: https://github.com/Enlixe/E-Spam/releases")
      print("Note: To copy from windows console: Right Click > Choose 'Mark' > Highlight the text > Use Ctrl-C")
      input("\nPress enter to Exit...")
      sys.exit()
    elif silentCheck == True:
      isUpdateAvailable = True
      return isUpdateAvailable

  elif parse_version(latestVersion) == parse_version(currentVersion):
    if silentCheck == False:
      print("\nYou have the latest version: " + currentVersion)
      input("\nPress enter to Exit...")
      sys.exit()
  else:
    if silentCheck == False:
      print("\nNo newer release available - Your Version: " + currentVersion + "  --  Latest Version: " + latestVersion)
      input("\nPress enter to Exit...")
      sys.exit()
    elif silentCheck == True:
      return isUpdateAvailable
      
##########################################################################################
##########################################################################################
###################################### MAIN ##############################################
##########################################################################################
##########################################################################################

def main():
  # Run check on python version, must be 3.6 or higher because of f strings
  if sys.version_info[0] < 3 or sys.version_info[1] < 6:
    print("Error Code U-2: This program requires running python 3.6 or higher! You are running" + str(sys.version_info[0]) + "." + str(sys.version_info[1]))
    input("Press Enter to exit...")
    sys.exit()

  spamError = False
  
  # Checks system platform to set correct console clear command
  # Clears console otherwise the windows terminal doesn't work with colorama for some reason  
  clear_command = "cls" if platform.system() == "Windows" else "clear"
  os.system(clear_command)
  
  # Initiates colorama and creates shorthand variables for resetting colors
  init(autoreset=True)
  S.R = S.RESET_ALL
  F.R = F.RESET
  B.R = B.RESET
  
  print("\n   Loading...\n")
  time.sleep(1)

  # Check for config file, load into dictionary 'config'
  config = load_config_file()
  try:
    configFileVersion = int(config['config_version'])
    if configFileVersion < configVersion:
      configOutOfDate = True
    else:
      configOutOfDate = False
  except:
    configOutOfDate = True

  os.system(clear_command)
  if config != None:
    if config['use_this_config'] == 'ask':
      if configOutOfDate == True:
        print(f"{F.LIGHTRED_EX}WARNING!{S.R} Your config file is out of date. If you don't generate a new one, you might get errors.")
      if choice(f"\nFound {F.YELLOW}config file{S.R}, use those settings?") == False:
        config = None
      os.system(clear_command)
    elif config['use_this_config'] == False:
      config = None
    elif config['use_this_config'] == True:
      pass
    else:
      print("Error C-1: Invalid value in config file for setting 'use_this_config' - Must be 'True', 'False', or 'Ask'")
      input("Press Enter to exit...")
      sys.exit()
      
  # Check for program updates
  if not config or config['auto_check_update'] == True:
    try:
      updateAvailable = check_for_update(version, silentCheck=True)
      os.system(clear_command)
    except:
      print(f"{F.LIGHTRED_EX}Error Code U-3 occurred while checking for updates. (Checking can be disabled using the config file setting) Continuing...{S.R}\n")
      updateAvailable = False
  else:
    updateAvailable = False
    os.system(clear_command)
    
  #----------------------------------- Begin Showing Program ---------------------------------
  print(f"{F.YELLOW}\n===================== YOUTUBE SPAMMER PURGE v" + version + f" ====================={S.R}")
  print("=========== https://github.com/ThioJoe/YouTube-Spammer-Purge ===========")
  print("================= Author: ThioJoe - YouTube.com/ThioJoe ================ \n")

  # Instructions
  print("Purpose: Lets you scan for spam comments and mass-delete them all at once \n")
  print("NOTE: It's probably better to scan a single video, because you can scan all those comments,")
  print("       but scanning your entire channel must be limited and might miss older spam comments.")

  # User selects scanning mode,  while Loop to get scanning mode, so if invalid input, it will keep asking until valid input
  print(f"\n---------- {F.YELLOW}Spamming Options{S.R} --------------------------------------")
  print(f"      1. Spam a {F.LIGHTBLUE_EX}Text{S.R}")
  print(f"      2. Spam an {F.LIGHTCYAN_EX}User{S.R}")
  print(f"-------------------------------------- {F.LIGHTRED_EX}Other Options{S.R} -------------")
  print(f"      3. Create your own config file to quickly run the program with pre-set settings")
  print(f"      4. Check For Updates\n")

  # Check for updates silently
  if updateAvailable == True:
    print(f"{F.LIGHTGREEN_EX}Notice: A new version is available! Choose 'Check For Updates' option for details.{S.R}\n")
  if configOutOfDate == True:
    print(f"{F.LIGHTRED_EX}Notice: Your config file is out of date! Choose 'Create your own config file' to generate a new one.{S.R}\n")

  # Make sure input is valid, if not ask again
  validMode = False
  validConfigSetting = True
  while validMode == False:
    if validConfigSetting == True and config and config['scan_mode'] != 'ask':
      scanMode = config['scan_mode']
    else:
      scanMode = input("Choice (1-4): ")

    # Set scanMode Variable Names
    validModeValues = ['1', '2', '3', '4', 'user', 'text', 'update', 'config']
    if scanMode in validModeValues:
      validMode = True
      if scanMode == "1" or scanMode == "text":
        scanMode = "text"
      elif scanMode == "2" or scanMode == "user":
        scanMode = "user"
      elif scanMode == "3":
        scanMode = "makeConfig"
      elif scanMode == "4":
        scanMode = "checkUpdates"
    else:
      print(f"\nInvalid choice: {scanMode} - Enter either 1, 2, 3 or 4. ")
      validConfigSetting = False

  # If chooses to spam text - Get text, and confirm with user
  if scanMode == "text":
    # Spam Message
    if validConfigSetting == True and config and config['spam_message'] != 'ask':
      spamMessage = config['spam_message']
    else:
      spamMessage = input("\nEnter your spam message: ")
    # Spam Amount
    if validConfigSetting == True and config and config['spam_amount'] != 'ask':
      spamAmount = config['spam_amount']
    else:
      spamAmount = input("Enter the amount of times you want to spam: ")
    if spamAmount.isdigit() == False:
      print(f"\nInvalid amount: {spamAmount} - Enter a number. ")
      spamAmount = input("Enter the amount of times you want to spam: ")   
    # Spam Interval
    if validConfigSetting == True and config and config['spam_interval'] != 'ask':
      spamInterval = config['spam_interval']
    else:
      spamInterval = input("Enter the amount of time you want to wait between each spam: ")
    if spamInterval.isdigit() == False:
      print(f"\nInvalid amount: {spamInterval} - Enter a number. ")
      spamInterval = input("Enter the amount of time you want to wait between each spam: ")
    # Begin Spamming
    print(f"Begin spamming:\n- Message: {spamMessage}\n- Spam Amount: {spamAmount} times\n- Spam Interval: {spamInterval}\nIn {F.LIGHTGREEN_EX}3 seconds{S.R}\n")
    time.sleep(3)
    for i in range(0,int(spamAmount)):
      pyautogui.typewrite(spamMessage + '\n')
      time.sleep(int(spamInterval));

  # If chooses to spam user - Get user, and confirm with user
  elif scanMode == "user":
    # Spam Message
    spamMessage = input("\nEnter user to spam: ")
    # Spam Amount
    if validConfigSetting == True and config and config['spam_amount'] != 'ask':
      spamAmount = config['spam_amount']
    else:
      spamAmount = input("Enter the amount of times you want to spam: ")
    if spamAmount.isdigit() == False:
      print(f"\nInvalid amount: {spamAmount} - Enter a number. ")
      spamAmount = input("Enter the amount of times you want to spam: ")   
    # Spam Interval
    if validConfigSetting == True and config and config['spam_interval'] != 'ask':
      spamInterval = config['spam_interval']
    else:
      spamInterval = input("Enter the amount of time you want to wait between each spam: ")
    if spamInterval.isdigit() == False:
      print(f"\nInvalid amount: {spamInterval} - Enter a number. ")
      spamInterval = input("Enter the amount of time you want to wait between each spam: ")
    # Begin Spamming
    print(f"Begin spamming:\n- Message: @{spamMessage}\n- Spam Amount: {spamAmount} times\n- Spam Interval: {spamInterval}\nIn {F.LIGHTGREEN_EX}3 seconds{S.R}\n")
    time.sleep(3)
    for i in range(0,int(spamAmount)):
      pyautogui.typewrite('@' + spamMessage + '\n' + '\n')
      time.sleep(int(spamInterval));

  # Create config file
  elif scanMode == "makeConfig":
    create_config_file()
    print("\nConfig file created: SpamConfig.ini - Open file with text editor to read instructions and change settings.")

  # Check for latest version
  elif scanMode == "checkUpdates":
    check_for_update(version)

# Runs the program
try:
  spamError = False
  main()
except:
  # traceback.print_exc()
  print("------------------------------------------------")
  if spamError == True:
    print("Error Message: " + "An Error Occured - Check the console for more details")
    input("\nPress Enter to Exit...")