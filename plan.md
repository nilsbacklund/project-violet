# ToDo for main loop and integration
## Red team
- loop for attacking
- saving data correctly in file, one big file with everything
- option to log everythin and save it correctly (to the shared 300GB folder)

## Blue team
- saving everyting
- renaming things

## Main.py
- base config for hoeypt
- loop new cofig (sessionID)
    - Generate new config from old data
    - set config to honeypot
    - run cupple of sessions (loop through red-llm)
        - save logs (one file per configuration)
    - format and extract interesting info from logs (lable/tactic + commands)
    - save configuration + lables

## To think about
- need to be able to stop and run