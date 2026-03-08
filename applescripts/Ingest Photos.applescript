on open dropped_items
	set personal_folder to "/Volumes/Photography/Personal"
	set script_path to "/Volumes/Photography/sort-photos.py"
	repeat with this_item in dropped_items
		set source_path to POSIX path of this_item
		if source_path ends with "/" then
			set source_path to text 1 thru -2 of source_path
		end if
		set cmd to "python3 " & quoted form of script_path & " --ingest " & quoted form of source_path & " " & quoted form of personal_folder
		try
			set result_output to do shell script cmd
			display dialog "Done!" & return & return & result_output buttons {"OK"} default button "OK" with title "Ingest Photos"
		on error err_msg
			display dialog "Error:" & return & return & err_msg buttons {"OK"} default button "OK" with title "Ingest Photos" with icon stop
		end try
	end repeat
end open

on run
	display dialog "Drop a memory card folder onto this app to ingest photos into your Personal folder." buttons {"OK"} default button "OK" with title "Ingest Photos"
end run
