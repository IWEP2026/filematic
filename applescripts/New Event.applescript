-- New Event.applescript
-- Double-click this app to create a new structured event folder.
-- It opens Terminal and walks you through 4 prompts:
--   Year, Shoot type, Client name, Shoot date
-- Then builds the full folder structure on your Photography SSD.
--
-- HOW TO COMPILE:
--   1. Open this file in Script Editor
--   2. File → Export → File Format: Application
--   3. Save as "New Event.app" wherever you like
--   4. Double-click the app to run

set script_path to "/Volumes/Photography/new-event.sh"

tell application "Terminal"
    activate
    do script "bash " & quoted form of script_path
end tell
