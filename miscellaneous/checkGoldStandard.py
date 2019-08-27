#!/usr/bin/python
import os
import bz2
import argparse
import re
import numpy as np

def levenshtein(seq1, seq2): #otherwise install & import the Levenshtein-module
    '''Code taken from https://stackabuse.com/levenshtein-distance-and-text-similarity-in-python/'''

    size_x = len(seq1) + 1
    size_y = len(seq2) + 1
    matrix = np.zeros ((size_x, size_y))
    for x in xrange(size_x):
        matrix [x, 0] = x
    for y in xrange(size_y):
        matrix [0, y] = y

    for x in xrange(1, size_x):
        for y in xrange(1, size_y):
            if seq1[x-1] == seq2[y-1]:
                matrix [x,y] = min(
                    matrix[x-1, y] + 1,
                    matrix[x-1, y-1],
                    matrix[x, y-1] + 1
                )
            else:
                matrix [x,y] = min(
                    matrix[x-1,y] + 1,
                    matrix[x-1,y-1] + 1,
                    matrix[x,y-1] + 1
                )
    return (matrix[size_x - 1, size_y - 1])

def titles_are_similar(gs_title, i_title):
    '''Returns true, if Levenshtein-distance is at most 1.
    In the future, title-names differing only by whitespaces and different dashes(hypen, en dash, em dash) shall not be counted towards the distance (todo!).'''

    ratio = levenshtein(gs_title, i_title) #check this for every type of dash!if only one ratio is <= 1, then return True
    if ratio <= 1:
        return True
    else:
        return False

def formulae_are_similar(gs_formula, i_formula):
    '''Returns true if formulae are the same after deleting every space characters(e.g. whitespaces, Latex-specifix space commands like "\," or "\!" and commas at the end of the formula) and ignoring different notations for single indices(=with and without curly brackets)
    Reason: Formulae from Dump and from Wikidata Query differ slightly (and both also differ from the Wikipedia html source code).
    Problems: Does not yet delete more Latex-specific spaces as well as Latex-specific commands like "\rm", '''

    #todo: delete Latex-specific commands like "\rm" in the following code line. these might appear as part of the index => "k_{\rm B}" -> "k_{\rm {B}}" (part of the formula of "Einstein relation (kinetic theory)" in the html-Code) does not work properly yet!

    #todo: delete "\n"

    #todo: two formulae "A=B=C" and "A=C" should probably be considered as being similar


    #delete Latex-spaces "\," and "\;" and "\!" and "\ ", they sometimes occur at the end before a comma in the Dump, but not in the html-code/GoldStandard            #test if more Latex-spaces from https://www.latex-kurs.de/kurse/Extra/Abstaende_in_Latex.pdf occur in formulae!
    gs_formula = re.sub(r"\\,", "", gs_formula)
    i_formula = re.sub(r"\\,", "", i_formula)
    gs_formula = re.sub(r"\\;", "", gs_formula)
    i_formula = re.sub(r"\\;", "", i_formula)
    gs_formula = re.sub(r"\\!", "", gs_formula)
    i_formula = re.sub(r"\\!", "", i_formula)
    gs_formula = re.sub(r"\\ ", "", gs_formula) #lookbehind to make sure we don't have a linebreak; counting the number of backslashes would be better to account for multiple linebreaks though!
    i_formula = re.sub(r"\\ ", "", i_formula)

    #ignore different notations for single indices, which can be written in two notations in Latex: "_i" or "_{i}" or "_\alpha" or "_{\alpha}"
    gs_formula = re.sub(r'([_^])(\\[a-zA-Z]+?)(\W)', r'\g<1>{\g<2>}\g<3>', gs_formula)
    gs_formula = re.sub(r'([_^])(\w)', r'\g<1>{\g<2>}', gs_formula)
    i_formula = re.sub(r'([_^])(\\[a-zA-Z]+?)(\W)', r'\g<1>{\g<2>}\g<3>', i_formula)
    i_formula = re.sub(r'([_^])(\w)', r'\g<1>{\g<2>}', i_formula)

    #delete comma (seen in the Dump) & dot (seen in the Dump) & semicolon at end
    gs_formula = re.sub(";$", "", gs_formula)
    gs_formula = re.sub(",$", "", gs_formula)
    gs_formula = re.sub("\.$", "", gs_formula)
    i_formula = re.sub(";$", "", i_formula)
    i_formula = re.sub(",$", "", i_formula)
    i_formula = re.sub("\.$", "", i_formula)

    #delete unnecessary single backslash at the end (seen in html code)
    gs_formula = re.sub(r"(\\\\)+\\$", "\g<1>", gs_formula) #delete single backslash, in case there are linebreaks before it
    gs_formula = re.sub(r"(?<=[^\\])\\$", "", gs_formula)   #delete single backslash without linebreak before it/that's not part of a linebreak
    i_formula = re.sub(r"(\\\\)+\\$", "\g<1>", i_formula)
    i_formula = re.sub(r"(?<=[^\\])\\$", "", i_formula)

    #delete whitespaces
    gs_formula = "".join(gs_formula.split()) #deletes all whitespaces(' \t\n\r\v\f'); this doesn't include e.g. "\t" from "\theta" as intended, since we have the raw formulae strings as input
    i_formula  = "".join(i_formula.split())


    #check if formulae are now equal and thus were similar at the beginning
    if gs_formula == i_formula:
        return True
    else:
        return False

def compare_files(input_file, gold_standard_file):
    '''Compares titles(or QIDs) & formulae from the two input files. Prints formulae from gold_standard_file that are missing in input_file.
    Also prints all formulae (that share the same title) that are different in the two files, if "-v" is used.
    Supports file-formats bz2 and txt.'''

    num_of_titles = {}
    num_of_titles[input_file] = 0
    num_of_titles[gold_standard_file] = 0
    TP = 0
    FP = 0
    FN = 0
    TN = 0

    missing_titles = []
    different_formulae = {} #maps titles to correct(Gold Standard) & wrong(input_file) formulae
    similar_formulae = {} #maps titles to correct(Gold Standard) & similar-but-not-exactly-the-same(input_file) formulae
    gs_dict = {} #maps titles to formulae from gold_standard_file
    i_dict = {} #maps titles to formulae from input_file

    #add title and formula to dict
    for filename in [input_file, gold_standard_file]:
        #open files depending on file-format
        file = None
        if filename.split(".")[-1] == "bz2":
            file = bz2.BZ2File(filename, 'r')
        else:
            file = open(filename, "r")

        #check if file contains titles or QIDs -> know which regex to search for
        file_contains_titles = False
        for line in file:
            if "<title>" in line:
                file_contains_titles = True
                break

        #reset file pointer to read file again
        file.seek(0)

        title = ""
        formula = ""
        for line in file:
            if (file_contains_titles == True) and ("<title>" in line): #line contains either  "<title>ABC</title>"  or   "<title>ABC"
                #delete empty spaces as well as "<title>" at the beginning of the line if it occurs
                if re.search(r'<title>(.*)', line) != None:
                    title = re.search(r'[\ ]*<title>[\ ]*(.*)', line).group(1)
                #delete empty spaces as well as "</title>" at the end of the line if it occurs
                if re.search(r'(.*)</title>', title) != None:
                    title = re.search(r'(.*)[\ ]*</title>[\ ]*', title).group(1)
                num_of_titles[filename] += 1
            elif (file_contains_titles == False) and (re.search(r'^Q[1-9][0-9]*[\ ]*[0-9]*[\ ]*$', line) != None): #line contains QID, e.g. Q1234
                title = re.search(r'^(Q[1-9][0-9]*)[\ ]*[0-9]*[\ ]*$', line).group(1)
            else: #line with formula
                formula = line
                #add title & formula to respective dict
                if filename == input_file:
                    if i_dict.get(title) == None: #key not found
                        i_dict[title] = formula.replace("\n", "")
                    else:
                        i_dict[title] += formula.replace("\n", "") #append formula to dict, since the formula spans multiple lines
                else: #filename == gold_standard_file
                    if gs_dict.get(title) == None: #key not found
                        gs_dict[title] = formula.replace("\n", "")
                    else: #key already exists, because the formula spans multiple lines
                        gs_dict[title] += formula.replace("\n", "") #append formula to dict, since the formula spans multiple lines
        file.close()

    #compare titles & formulae from the two dictionaries
    for gs_title, gs_formula in gs_dict.items():
        num_of_title_matches = 0 #to search for missing titles in i_file, possibly due to strange characters in the title => they weren't found by wikiFilter.py or find_formula.py
        for i_title, i_formula in i_dict.items():
            if (gs_title == i_title):# or titles_are_similar(gs_formula, i_formula):
                num_of_title_matches += 1
                if num_of_title_matches == 1:
                    if gs_formula == i_formula:
                        if gs_formula == "":
                            TN += 1
                        else:
                            TP += 1
                    elif formulae_are_similar(gs_formula, i_formula):
                        similar_formulae[gs_title] = [gs_formula, i_formula]
                    else:
                        different_formulae[gs_title] = [gs_formula, i_formula]
                elif num_of_title_matches > 1:
                    print("ERROR! Title appeared more than once in input_file: ", gs_title)

        if num_of_title_matches == 0:
            missing_titles.append(gs_title)

    #error handling
    if num_of_titles[gold_standard_file] - num_of_titles[input_file] < len(missing_titles):
        print("ERROR! Number of found titles doesn't match. Some of the titles of input_file don't match with those from gold_standard_file, probably because of special characters that have been changed for regex search( '-' to '.' etc) or because the the wikipedia titles changed. It can also be that the last line(formula) of input_file.txt is empty(=no formula found) - in that case add another empty line at the end! This needs to be fixed manually in the gold_standard_file. \n Another (unlikely) cause might be a duplicated title in the input_file. \n It could also be that you mixed up the input file with the gold standard file.")
        print("num_of_titles[gold_standard_file]", num_of_titles[gold_standard_file])
        print("num_of_titles[input_file]", num_of_titles[input_file])
        print("len(missing_titles)", len(missing_titles))
    elif num_of_titles[gold_standard_file] - num_of_titles[input_file] > len(missing_titles):
        print("ERROR! Number of found titles doesn't match at all. This shouldn't have happened.")
        print("num_of_titles[gold_standard_file]", num_of_titles[gold_standard_file])
        print("num_of_titles[input_file]", num_of_titles[input_file])
        print("len(missing_titles)", len(missing_titles))

    #print results
    if len(similar_formulae) != 0:
        print("Similar formulae: ")
        for title in similar_formulae.keys():
            print("Title " + str(title) + " has similar formulae:")
            print("   " + '"' + similar_formulae[title][0] + '"')
            print("   " + '"' + similar_formulae[title][1] + '"')
        print("")
    if len(different_formulae) != 0:
        for title in different_formulae.keys():
            if (different_formulae[title][0] != "") and (different_formulae[title][1] == ""):
                FN += 1
            else: #there either is no defining formula or the wrong formula was found
                FP += 1
            if args.verbosity_level > 1:
                print(title + " has two different formulae:\n   " + '"' + different_formulae[title][0] + '"'  + " in Gold Standard,"+ "\n   " + '"' + different_formulae[title][1] + '"'  + " in input file.")
        print("")
    print("Number of titles with different formulae (FP+FN) = " + str(FP+FN) + ", FP = " + str(FP) + ", FN = " + str(FN))
    print("Number of TP(similar formulae not included) = " + str(TP))
    print("Number of similar formulae = " + str(len(similar_formulae)))
    print("Number of TN = " + str(TN))
    print(str(len(missing_titles)) + " missing titles: " + str(missing_titles))


if __name__ == '__main__':  # When the script is self run
    parser = argparse.ArgumentParser(description="Compares the titles and formulas in input_file with the Gold Standard file; \n The files should be build like this: \n\n <title>SomeWikipediaTitle</title>\\n SomeFormulaWithoutEnclosingMathTags\\n <title>SomeWikipediaTitle2</title>\\n SomeFormulaWithoutEnclosingMathTags2\n\n;     Note that the titles must include a dot(.) for every hyphen(-) or other strange character regex cannot properly deal with. Apostrophs(') are excluded from this and can be added as usual.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-f', '--filename', help='the input_file to compare against the Gold Standard file(specify with -g)',
        default='output.txt', dest='input_file')
    parser.add_argument('-g', '--goldstandard', help='the Gold Standard file to compare against',
            default='Gold Standard.txt', dest='gold_standard_file')
    args = parser.parse_args()

    compare_files(args.input_file, args.gold_standard_file)
