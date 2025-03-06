## KNOWN ISSUES OF THE MAIN EXP CODE

- If the ITI time is as low or lower than the door motor movement time (approx 2200ms) then the arduino will not move to the next trial. Arduino currently
waits for the door to move up to understand that the trial is over. As ITI will generally be higher than this, it is unlikely to cause issues, but good to know.
