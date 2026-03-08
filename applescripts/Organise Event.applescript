-- Organise Event.applescript
-- Drag an existing event folder onto this app to restructure it.
-- It moves all RAWs + XMPs into Unedited RAWs/ and creates
-- Completed/Best Images/ and _SESSION-INFO.md automatically.
--
-- HOW TO COMPILE:
--   1. Open this file in Script Editor
--   2. File → Export → File Format: Application
--   3. Save as "Organise Event.app" wherever you like
--   4. Drag any event folder onto the app icon to run

set script_path to "/Volumes/Photography/organise-existing-event.sh"

on open dropped_items
    set script_path to "/Volumes/Photography/organise-existing-event.sh"
    repeat with item_ref in dropped_items
        set folder_path to POSIX path of item_ref
        tell application "Terminal"
            activate
            do script "bash " & quoted form of script_path & " " & quoted form of folder_path
        end tell
    end repeat
end open
