These are Oliver's re-writes of Yao/Alex's scripts.


Of note:
How do we handle moiety folder naming in the simulation folder when two positions add the same moiety? A: Manually. I need to include the residue number in the folder name.

They want to include crystallographic water but it didn't work for them.

Manual preprocessing to remove partial occupancy residues and rename carb to ATOM instead of HETATM is necessary. I plan to add my preprocessor in an early step. 

COMPLETE: Manually creating and adding the charges in charges.txt. Fixed by a script here, but can it handle multiple Libraries? no. Update: Yes.

Because of having to handle different PATHs in the website, convert everything to relative where possible.
