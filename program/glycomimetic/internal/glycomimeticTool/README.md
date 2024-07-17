Glycomimetics
Compilation in ./src:
bash compile.sh

main.exe will be created in the parent directory glycomimetics

Sample Usage:
./main.exe -c receptor_pdbqts/Gordon_HA_4BGX/4bgx_chainA_49_267.pdbqt -a 269_C5_N5_C10-moieties/pdbqt/Gordon_HA_4BGX-2.pdbqt -i 30 -t 4 -o output_files/literature_moieties/Gordon_HA_4BGX/me/2/ -l glycomimetic.log
./main.exe -c receptor_pdbqts/Murphy_HA_3ubq/3ubq_chainC_55_270_N9.pdbqt -a 326_N5_C10_C11-moieties/pdbqt/Murphy_HA-N5_CF3.pdbqt -a 326_C9_N9_HO9-moieties/pdbqt/Murphy_HA-N9_1.pdbqt-326_C7_C8_C9_N9-link:180 -i 10 -t 4 -o output_files/literature_moieties/Murphy_HA_3ubq/1
Options:
-c file path to a pdbqt file of the co-complex
-a each such option specifies what to do with each open valence atom
    This option is first tokenized with dash "-"
    Token 1 is futher tokenized by underline "_":Resindex_Atom1Name_OpenValenceAtomName_AtomToReplace
        Resindex:the residue index of the open valence atom, as in the input pdb file
        Atom1Name:The first atom of the torsion formed by creatin a new bond
        OpenValenceAtomName: The name to the atom which will bond with a new R group.
        AtomToReplace: The name of the atom and all its downstream atoms that will be replaced by the new R group.
    Token 2: path to the R group libary files to apply to this open valence position.
    Token 3: a name patten which the library file names must contain in order to be analyzed. To look at all R groups, simply put "pdbqt"
    Token 4+ (optional) specifies any torsion angles to rotated that's not the linkage bond and in the R group. They are futher tokenized by underscore "_": Resindex_Atom1_Atom2_Atom3_Atom4:number
        Resindex: The residue index that contains atom1-4. This does have to caveat of confining all 4 atoms in the same residue. 
        Atom1-4: The names of the four atoms of this torsion angle. Atoms on the Atom4 side will be rotated.
        Special case: the linkage torsion does not belong to the same residue, and you can use the "link" keyword to specify the linkage torsion, whose atom 1 and 2 are determined with this -a option, and whose                      atom 3 and 4 are determined in the moiety libaray file. 
        If colon (:) exists, a number X follows to set this tosion to X degrees. You use this if you have some prior knowledge that this bond is not freely rotatable but instead should take a specific value. 
        
-i X. If gridsearching is used to compute rotamer, grid size is set to X degrees so that each torsion has (360/i) values. I've moved to monte carlo searching so give this any value. 
-t X. Use X threads for conformational searching. 
-o path. Path where all the output files will be written in.
-l logfie. Path to a log file. If alredy exists, will be overwritten each time program executes. 

    

        
    
