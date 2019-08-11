#!/usr/bin/python
import os
import bz2
import argparse
import re
import urllib2
from HTMLParser import HTMLParser

title_in_other_languages = {}
list_of_title_in_other_languages = []
def get_all_languages_titles(titles_file, languages):
    '''Translates titles from txt-file to titles in given languages.
    Function is no longer used in favor of using QIDs.'''

    #get titles to translate
    titles = []
    f = open(titles_file, 'r')
    for line in f:
        line = line.replace("\n", "")
        titles.append(line)

    for title in titles:
        title_in_other_languages = get_title_in_other_languages(title, "en", languages)
        list_of_title_in_other_languages.append(title_in_other_languages)
    return list_of_title_in_other_languages

def get_title_in_other_languages(title, title_language, other_languages):
    '''Translates Wikipedia title from the specified language(e.g. en, de, fr, it,...) to other languages.
    Uses normalized titles via:
    https://www.wikidata.org/w/api.php?action=wbgetentities&sites=enwiki&titles=WIKIPEDIA-TITLE&normalize=1
    instead of
    https://www.wikidata.org/w/api.php?action=wbgetentities&sites=enwiki&titles=WIKIPEDIA-TITLE
    as this fixes wrong initial character capitalization, underscores (and possible more) (which may occur due to changed wikipedia titles), as can be read here:
    https://stackoverflow.com/questions/37024807/how-to-get-wikidata-id-for-an-wikipedia-article-by-api
    This function is no longer used in favor of translating QIDs(not titles) via get_QID_and_lang_to_title().'''

    def get_html_code(title, title_language):
        '''returns html code from "https://www.wikidata.org/w/api.php?action=wbgetentities&sites=' + title_language + 'wiki&titles=' + title + '&normalize=1"'''
        def open_url(url):
            try:
                req = urllib2.Request(url)
                http_response_object = urllib2.urlopen(req)
                return http_response_object
            except Exception as e:
                print("Error with url: " + url)
                print(e)
                print("\n")

        url = 'https://www.wikidata.org/w/api.php?action=wbgetentities&sites=' + title_language + 'wiki&titles=' + title + '&normalize=1'

        http_response_object = open_url(url)
        html_as_bytes = http_response_object.read() #type: bytes
        html = html_as_bytes.decode("utf8") #type: str

        return html

    title = title.replace(" ", "%20") #anything else to replace for html in this url-part?
    title = title.replace("<title>", "")
    title = title.replace("</title>", "")

    html = get_html_code(title, title_language)
    html = html.split("\n")

    language_of_title = None
    title_in_other_languages = {}
    for line in html:
        #todo: check for possible redirect("from:", "to:") and notify user of changed title
        if '&quot;missing&quot;' in line:
            print("ERROR! title " + title + " from language " + title_language + " was not found via the Wikidata API.")
        if ('&quot;code&quot;' in line) and ('&quot;params-illegal&quot;' in line):
            print("ERROR! title " + title + " from language " + title_language + " resulted in a 'params-illegal'-Errorcode.")
        if '&quot;descriptions&quot;' in line: #solves the problem that multiple lines consist of '"language": "en"', but only the first occurence is followed by the title
            break
        if language_of_title != None: #current line contains the title
            title_in_other_languages[language_of_title] = re.search("\>\&quot\;(.*?)\>\&quot\;(.*?)\&quot\;\<\/span\>$", line).group(2)
            language_of_title = None
        else:
            #check for errors
            if "&quot;language&quot;</span>" in line:
                for language in other_languages:
                    if "&quot;" + language + "&quot;</span>" in line:
                        if language_of_title != None:
                            print("ERROR! Multiple languages in line. This should never appear! Maybe the API changed => you need to manually change the code!")
                            print("Line:")
                            print(line)
                            print("Second(or third or...) language found: " + language)
                            print("Complete html code:")
                            print(html)
                        language_of_title = language #next line contains the title

    return title_in_other_languages

def get_QID_and_lang_to_title(QIDs, languages=[]):
    '''Converts list of QIDs to a dictionary(named "QID_and_lang_to_title") mapping each tuple (QID, language) to it's corresponding title, for all specified languages.
    If no languages are specified, all languages available for a QID will be included.
    Titles returned will be unescaped (e.g. "&#039;" becomes "'").
    Only gets titles for languages named "enwiki", "dewiki",...; does not match "enwikiquote", "enwikibooks",...!'''

    def get_html_code(QID):
        '''returns html code from "https://www.wikidata.org/w/api.php?action=wbgetentities&format=xml&props=sitelinks&ids=" + QID'''
        def open_url(url):
            try:
                req = urllib2.Request(url)
                http_response_object = urllib2.urlopen(req)
                return http_response_object
            except Exception as e:
                print("Error with url: " + url)
                print(e)
                print("\n")

        url = 'https://www.wikidata.org/w/api.php?action=wbgetentities&format=xml&props=sitelinks&ids=' + QID

        http_response_object = open_url(url)
        html_as_bytes = http_response_object.read() #type: bytes
        html = html_as_bytes.decode("utf8") #type: str

        #for documentation purposes
        file = open("get_QID_and_lang_to_title " + QID, "w")
        file.write(html)
        file.close()

        return html

    QID_and_lang_to_title = {}
    for QID in QIDs:
        #search html code and look for titles
        html = get_html_code(QID)
        html = html.split("\n")
        for line in html:
            if "<sitelink site=" in line:
                wikis = re.findall('site=\"(.*?)\"', line)
                titles = re.findall('title=\"(.*?)\"', line)

                #exctract languages from wikis
                wiki_languages = []
                new_titles = [] #only includes titles from desired wikis
                for i, wiki in enumerate(wikis):
                    if wiki.endswith('wiki') == True:  #only matches wikis named "enwiki", "dewiki",...; does not match "enwikiquote", "enwikibooks",...!
                        wiki_languages.append(wiki[:-4])
                        new_titles.append(titles[i])
                titles = new_titles

                for language, title in zip(wiki_languages, titles):
                    if (language in languages) or languages == []: #languages == [] in case you want to get the titles of all languages
                        unescaped_title = HTMLParser().unescape(title) #unescapes title, e.g. "&#039;" becomes "'"
                        QID_and_lang_to_title[(QID, language)] = unescaped_title

    return QID_and_lang_to_title

def get_titles_for_language(specified_language, QID_and_lang_to_title):
    '''Searches QID_and_lang_to_title (which maps the tuple (QID, language) to its title) for every title of the specified language.
    Returns found titles as list.'''

    titles = []
    for (QID, language), title in QID_and_lang_to_title.items():
        if language == specified_language:
            titles.append(title)

    return titles

def read_QIDs_from_file(QID_file):
    '''The QID_file consists of formulae and QIDs. This function extracts the QIDs from it and returns them in a list.
    Works for txt-files where each line only contains
    <title>SOME-TITLE</title>
    or
    SOME-FORMULA-BUT-NO-TITLE
    No mixed line of title and formula is allowed.'''

    QIDs = []
    f = open(QID_file, 'r')
    for line in f:
        if re.match("^Q[1-9][0-9]*$", line) != None: #line consists of only a QID like "Q1234"
            line = line.replace("\n", "")
            QIDs.append(line)

    return QIDs

def get_ifiles_and_lang(args_file, args_dir):
    '''Uses user input(input files and output directory) to determine which bz2-files to process
    - already processed bz2-files(=those found in the output directory) will be skipped.
    If no input files are specified, every bz2-file in the current directory will be used as input file.
    The input files need to begin with the language code followed by "wiki" -> "enwiki", "dewiki",...
    Returns a list of the input files together with a list of the language codes.
    '''

    bz2_files = []
    languages = []
    if args_file == '': #use all .bz2-files as input, except for the case when the result was already calculated before and saved in the given output-dir
        files_in_current_dir = None
        for root, directories, f_names in os.walk("./"):
            files_in_current_dir = f_names[:]
            break
        #remove files where the result has already been calculated & saved before
        for root, directories, f_names in os.walk(args_dir):
            for filename in f_names:
                if filename in files_in_current_dir:
                    files_in_current_dir.remove(filename)
                    print("Result for " + filename + " has already been calculated before and thus will be reused. If you don't want this behaviour, either delete/move the file from the given output-directory or choose another output-directory!")
            break
        #only add .bz2-files
        for filename in files_in_current_dir:
            if filename.endswith(".bz2"):
                bz2_files.append(filename)
                languages.append(filename.split("wiki")[0])
    else: #use only given file(s) as input
        for f in args_file:
            bz2_files.append(f)
            languages.append(f.split("wiki")[0])

    return bz2_files, languages

def get_ofiles_and_lang(args_dir):
    '''Uses all bz2-files in the given output directory to determine the result_files(already processed output files).
    These are not necessarily the same as the input files in case we reuse already processed output files.
    Returns the result_files as well as result_languages(=language codes = beginning of the filename, followed by "wiki").'''

    result_files = [] #not necessary the same as bz2_files(=input files) in case we reused results
    result_languages = []
    for root, directories, f_names in os.walk(args_dir):
        for f_name in f_names:
            if f_name.endswith(".bz2"):
                result_files.append(f_name)
                result_languages.append(f_name.split("wiki")[0])
        break

    return result_files, result_languages

def get_formulae_dict(QID_and_lang_to_title, result_files, args_tags, args_dir, args_verbosity_level):
    '''Checks which formulae occur how often for each article in all its languages (on a single site, a formula will be counted only once).
    Returns formulae_dict - mapping each tuple (QID and most-common-formula) to number-of-occurences-of-formula.'''

    formulae_dict = {} #mapping the tuple (QID, formula) to the number of occurrences across different sites
    tags = args_tags.split(',')

    for f_name in result_files:
        language = f_name.split("wiki")[0]
        file = bz2.BZ2File(os.path.join(args_dir, f_name), 'r')
        found_QIDs = [] #for non-found-QIDs the formula "" will be saved - some titles will not be found a) if you prefiltered the bz2-file to only contain pages with formulae (=>it is correct to choose "" as the formula)   b) if you have an old Dump and the title changed (=>beware that you might not want "" as the formula in that case!)
        for line in file:
            #search for title to save corresponding QID with the formulae that are contained in the lines after the title
            if "<title>" in line:
                current_title = line[line.find("<title>")+7  :  line.find("</title>")]
                current_QID = None
                current_tag = None
                current_formula = ""
                formulae_found = [] #lists all formulae for the current title => every formula will only be counted once per page (this does currently not take similar formulae into account!->use e.g. formulae_are_similar()!)

                #get QID of found title
                for (QID, lang), title in QID_and_lang_to_title.items():
                    if (lang == language) and (title == current_title.decode('utf8')):
                        current_QID = QID
                        found_QIDs.append(QID)
                        if args_verbosity_level > 1:
                            print("Found title: ", QID, lang, title)

            elif line == "\n": #no formula was found in the Wikipedia article, because there either is no defining formula or it did not have a formula_indicator
                #add empty formula to dict
                current_formula = ""
                if current_formula not in formulae_found: #delete this if-clause all 3 times in this function if you want to count a reoccurring formula on one page multiple times instead of once
                    formulae_found.append(current_formula)
                    if formulae_dict.get((current_QID, current_formula)) == None: #formula didn't occur yet
                        formulae_dict[(current_QID, current_formula)] = 1
                    else:
                        formulae_dict[(current_QID, current_formula)] += 1

            else: #line contains formula
                for tag in tags:
                    #a) formula ends in current line
                    if (current_tag != None) and (tag == current_tag):
                        if (line.find("<"+tag+">") == -1) and (line.find("</"+tag.split(" ")[0]+">") != -1):#deals with <math chem> being closed as </math>
                            current_formula += line[  :  line.find("</"+tag.split(" ")[0]+">")]
                            #add formula to dict
                            if current_formula not in formulae_found: #every formula will only be counted once per page
                                formulae_found.append(current_formula)
                                if formulae_dict.get((current_QID, current_formula)) == None: #formula didn't occur yet
                                    formulae_dict[(current_QID, current_formula)] = 1
                                else:
                                    formulae_dict[(current_QID, current_formula)] += 1

                            current_formula = ""
                            current_tag = None
                            break

                for tag in tags:
                    #b) formula completely contained inside the current line
                    if (line.find("<"+tag+">") != -1) and (line.find("</"+tag+">") != -1):
                        current_formula = line[line.find("<"+tag+">") + 2 + len(tag)   :    line.find("</"+tag+">")]
                        #add formula to dict
                        if current_formula not in formulae_found: #every formula will only be counted once per page
                            formulae_found.append(current_formula)
                            if formulae_dict.get((current_QID, current_formula)) == None: #formula didn't occur yet
                                formulae_dict[(current_QID, current_formula)] = 1
                            else:
                                formulae_dict[(current_QID, current_formula)] += 1

                        current_formula = ""

                    #c) formula starts in current line
                    if line.rfind("<"+tag+">") > line.rfind("</"+tag+">"): #last opening tag after last closing tag
                        current_formula = line[line.rfind("<"+tag+">") + 2 + len(tag)   : ]
                        current_tag = tag

                    #d) formula continues in current & next line
                    if (current_tag != None) and (tag == current_tag):
                        if (line.find("<"+current_tag+">") != -1) and (line.find("</"+current_tag+">") != -1):
                            current_formula += line

        #choose "" as the formula for every non-found-title
        for (QID, lang), title in QID_and_lang_to_title.items():
            if (lang == language) and (QID not in found_QIDs):
                if args_verbosity_level > 0:
                    print("Title '" + title.encode('utf8') + "' of language '" + language + "' was not found in the output-bz2-file, thus '' will be used as the found formula. This is probably your intention (=if the page didn't contain a formula), but it might be that the title changed, because you use an old dump!")
                current_formula = ""
                if formulae_dict.get((QID, current_formula)) == None: #formula didn't occur yet
                    formulae_dict[(QID, current_formula)] = 1
                else:
                    formulae_dict[(QID, current_formula)] += 1

    return formulae_dict

def extract_titles_and_formulae(filename, splitsize, dir, tags, keywords):
    ''' The function gets the filename of the xml.bz2-file as input
    and returns every formula of each page that has a title(=keyword) '''

    formulae_indicators = ['=', '<', '>', '\leq', '\geq', '\approx', '\equiv']#todo: consider adding more!  #todo:if no formula_indicator is found, choose first "formula"(that is longer than a few characters, so it won't be just a variable)!
    titles_found = [] #to check for missed titles

    if tags != '':
        tags = tags.split(',')
    else:
        tags = []

    # Check and create chunk diretory
    if not os.path.exists(dir):
        os.mkdir(dir)
    # Counters
    pagecount = 0
    filecount = 1
    header = ""
    footer = "</mediawiki>"
    title_and_formulae = ""
    # open chunkfile in write mode
    chunkname = os.path.join(dir, filename)
    chunkfile = bz2.BZ2File(chunkname, 'w')
    # Read line by line
    bzfile = bz2.BZ2File(filename)

    # the header
    for line in bzfile:
        header += line
        if '</siteinfo>' in line:
            break

    # and the rest
    for line in bzfile:
        try:
            line = line.decode("utf8") #probably faster to use python3 and specify encoding=utf8 in bz2.open()!  the bz2 module in python3 also supports multistreaming :)
        except Exception as e:
            print(e)
            print("   decoding-ERROR! This shouldn't happen as the dump is supposed to be UTF-8 encoded. The error is in line:")
            print(line)

        if '<page' in line: #start of new wikipage
            title_and_formulae = "" #string consisting of the title of page(that has a matching title) and all formulae
            keyword_matched = 0
            current_tag = None #the tag of the current formula spanning multiple lines
            check_for_multiple_line_formula = 0

        #search for title
        if keyword_matched == 0:   #no need to check for other matches, if keyword_matched=1
            for keyword in keywords:
                if keyword in line:
                    title_and_formulae = title_and_formulae + line.replace("\n", "").lstrip()
                    if keyword_matched == 0:
                        titles_found.append(keyword)
                    keyword_matched = 1

        #search for formulae
        if keyword_matched == 1:
            #search for formula parts(due to a formula spanning multiple lines)
            for tag in tags:
                if ('&lt;' + tag + '&gt;' in line) or (current_tag != None): # = either a formula begins in this line or we are already in a formula
                    check_for_multiple_line_formula = 1
            if check_for_multiple_line_formula == 1:
                #find rest of formula from last line (if it exists)
                for tag in tags:
                    if tag == current_tag: #only True, if a formula didn't end in the last line
                        if line.find('&lt;/'+tag+'&gt;') == -1: #checks if formula ends in another line <=> tag not found
                            #doublecheck if there really is not a single tag in the current line - happens, iff closing tag is different from opening tag(as is the case with <math chem>...</math>) or the closing tag is misspelled or consists of extra spaces(as is the case with ~10 formulae in the whole enwiki)
                            tag_and_position = [] #lists first found tag of the current line and the position of its occurence -> position of the first tag determines end of formula; remember: the found tag should be a closing tag of current_tag, but might not be due to e.g. a misspelling
                            for tag2 in tags:
                                if line.find('&lt;/'+tag2) != -1: #closing tag found
                                    if tag_and_position == []:
                                        tag_and_position = ['&lt;/'+tag2, line.find('&lt;/'+tag2)]
                                    else: #already found a tag => find out, which tag occured first
                                        if line.find('&lt;/'+tag2) < tag_and_position[1]:
                                            tag_and_position = ['&lt;/'+tag2, line.find('&lt;/'+tag2)]

                                if line.find('&lt;'+tag2) != -1: #opening tag found
                                    if tag_and_position == []:
                                        tag_and_position = ['&lt;'+tag2, line.find('&lt;'+tag2)]
                                    else: #already found a tag => find out, which tag occured first
                                        if line.find('&lt;'+tag2) < tag_and_position[1]:
                                            tag_and_position = ['&lt;'+tag2, line.find('&lt;'+tag2)]

                            if tag_and_position == []:  #there really is no closing tag in the current line
                                title_and_formulae = title_and_formulae + "\n" + line.replace("\n", "")
                            else:
                                if (args.verbosity_level > 0) and (current_tag != "math chem"): #"<math chem>" always gets closed with "</math>", so there is no need to notify the user in that case
                                    print("Unexpectedly found tag " + tag_and_position[0] + " (to opening tag " + current_tag + " ) in line " + line + "!")
                                title_and_formulae = title_and_formulae + "\n" + line[0:tag_and_position[1]] + "</"+tag_and_position[0]+">"
                                current_tag = None

                        else: #formula ends in this line
                            title_and_formulae = title_and_formulae + "\n" + line.split(r'&lt;/'+tag+'&gt;')[0] + "</"+tag+">" #does not find tags with spaces / misspelled tags yet!
                            current_tag = None

            #search for formula that lies completely inside the current line
            for tag in tags:
                if ('&lt;' + tag + '&gt;' in line):
                    pagecount += 1
                    formulae = re.findall(r'&lt;' + tag + r'&gt;(.*?)&lt;/' + tag + r'&gt;', line) #".*?" results in nongreedy search = shortest match
                    for formula in formulae:
                        for indicator in formulae_indicators:
                            if indicator in formula:# => it is a "real" formula, not just a variable
                                title_and_formulae = title_and_formulae + "\n" + "<"+tag+">" + formula + "</"+tag+">"

            if check_for_multiple_line_formula == 1:
                #find formula beginning in this line, but ending in the next
                for tag in tags:
                    if current_tag == None:
                        if line.rfind('&lt;'+tag+'&gt;') > line.rfind('&lt;/'+tag+'&gt;'): #last opening tag is after the last closing tag
                            title_and_formulae = title_and_formulae + "\n" + "<"+tag+">" + (line.split(r'&lt;'+tag+'&gt;')[-1]).replace("\n", "")
                            current_tag = tag

            check_for_multiple_line_formula = 0

        if '</page>' in line:
            title_and_formulae += "\n"

            #add empty line when no formula was found
            title_and_formulae_wo_l = title_and_formulae.replace("\n", "")   #title_and_formulae without a linebreak
            if title_and_formulae_wo_l[len(title_and_formulae_wo_l)-8:len(title_and_formulae_wo_l)] == "</title>": #title_and_formulae_wo_l ends with "</title"  <=>  no formula found
                title_and_formulae += "\n"

                if args.verbosity_level > 1:
                    try:
                        print("No formula found for title: " + title_and_formulae.encode('utf8'))
                    except Exception as e:
                        print(e)

            if keyword_matched == 1:
                title_and_formulae = title_and_formulae.encode("utf8")
                chunkfile.write(title_and_formulae)

                if args.verbosity_level > 1:
                    print(title_and_formulae)
                title_and_formulae = ""

        if pagecount > splitsize:
            if args.verbosity_level > 1:
                print("New bz2-file number " + pagecount + " since number of matched pages reached splitsize = " + splitsize)
            chunkfile.close()
            pagecount = 0
            filecount += 1
            chunkfile = bz2.BZ2File(chunkname(filecount), 'w')
            chunkfile.write(header)
    try:
        chunkfile.close()
    except:
        print('File already closed.')


    #check if every title was found
    if len(titles_found) != len(keywords):
        print("Error! Found " + str(len(titles_found)) + " titles of " + str(len(keywords)) + ". This should not happen unless you prefiltered the input-bz2-file(s) (e.g. filtered all pages with <math>-tags) or use an old Dump!")
        if args.verbosity_level > 1:
            print("   Titles found: " +  str(titles_found))
            print("   All titles: " + str(keywords))
        #check which titles were not found
        if args.verbosity_level > 0:
            for title in keywords:
                if title not in titles_found:
                    try:
                        print("   Title '" + title.encode('utf8') + "' was not found in the input-bz2-file.")
                    except Exception as e:
                        print(e)

if __name__ == '__main__':  # When the script is self run
    parser = argparse.ArgumentParser(description='Extract all formulae (defined as having a formula_indicator) from the wikipages that contain the titles corresponding to the given QIDs(loaded via "-Q"), in all specified languages(corresponding to the beginning of the bz2-filenames, e.g. "enwiki....bz2"). Afterwards extracts the most common formula for a wikipedia page (in all languages specified). Formulae occuring multiple times for a wikipedia page(in a single language) are counted only once!',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-f', '--filename', help='The bz2-file(s) to be filtered. Default: Use all bz2-files in current folder.',
        default='', type=str, dest='file', nargs='*')
    parser.add_argument('-s', '--splitsize', help='The number of pages contained in each split.',
        default=1000000, type=int, dest='size')
    parser.add_argument('-d', '--outputdir', help='The output directory name.',
        default='wout', type=str, dest='dir')
    parser.add_argument('-Q', '--QID_file', help='QID-file, containing one QID (e.g. "Q1234") in each line(other lines without QIDs can be mixed in). They will be translated to the titles in their respective languages and "<title>SOME_TITLE</title>" will be used as keywords. The languages will be taken from the beginning of the filenames, which thus must start with "enwiki"/"dewiki"/... for english/german/... ! "enwikibooks", "enwikiquote" etc. are not allowed!!!',
        default='', type=str, dest='QID_file')
    parser.add_argument('-t', '--tagname', help='Comma separated string of the tag names to search for; no spaces allowed.',
        default='math,ce,chem,math chem', type=str, dest='tags')
    parser.add_argument("-v", "--verbosity", action="count", default=0, dest='verbosity_level')
    parser.add_argument('-T', '--template', help='include all templates',
        action="store_true", dest='template')#default=False

    args = parser.parse_args()

    #determine input bz2-file(s) & corresponding language(s)
    bz2_files, languages = get_ifiles_and_lang(args.file, args.dir)
    print(str(len(bz2_files)) + " Input files: " + str(bz2_files))
    print(str(len(languages)) + " Languages: " + str(languages))

    #get QIDs
    QIDs = read_QIDs_from_file(args.QID_file)
    QID_and_lang_to_title = get_QID_and_lang_to_title(QIDs, languages)
    if args.verbosity_level > 0:
        print("\n")
        print("QID_and_lang_to_title (len=" + str(len(QID_and_lang_to_title)) + ") for extracting all formulae from bz2-files :")
        print(QID_and_lang_to_title)
        print("\n")

    #extract titles with all formulae from bz2-files
    for filename in bz2_files:
        language = filename.split("wiki")[0]
        titles = get_titles_for_language(language, QID_and_lang_to_title)
        if args.verbosity_level > 0:
            print("The following titles exist in language " + language + ":\n" + str(titles) + "\n")
        print(str(len(titles)) + " pages (of " + str(len(QIDs)) + " QIDs) exist for language " + language + ", equaling " + str(float(len(titles))/float(len(QIDs)) * 100) + "%. If this percentage is too low for most of your languages, you might need to add more languages to get good results!")
        if len(titles) == 0:
            print("No wikipedia pages matching the QIDs exist for language " + language + "! This can happen with few QIDs (here " + str(len(QIDs)) + " )or small wikis.")

        keywords = [ "<title>" + title + "</title>" for title in titles]
        extract_titles_and_formulae(filename, args.size, args.dir, args.tags, keywords)
        print("Done with file: " + filename)


    #find bz2-files containing the results(all formulae for each article); needed in case we reuse results
    result_files, result_languages = get_ofiles_and_lang(args.dir)
    print("Checking " + str(len(result_files)) + " files for similar formulae: " + str(result_files))
    #calculate QID_and_lang_to_title again, in case we are reusing results
    if languages.sort() != result_languages.sort():
        QID_and_lang_to_title = get_QID_and_lang_to_title(QIDs, result_languages) #has to be called again in case we reused results <=> not all languages are already included in QID_and_lang_to_title
        if args.verbosity_level > 0:
            print("\nQID_and_lang_to_title (len=" + len(QID_and_lang_to_title) + ") to be checked for most common formula:")
            print(QID_and_lang_to_title)
            print("\n")


    #check which formulae occur how often for each QID (on a single wikipage, a formula will be counted only once)
    formulae_dict = get_formulae_dict(QID_and_lang_to_title, result_files, args.tags, args.dir)
    if args.verbosity_level > 1:
        print("\nAll formulae (QID, formula, #occurences):")
        print(formulae_dict)
        print("\n")

    #find biggest number of occurrences for each QID
    print("Now checking for most common formula...")
    most_common_formula_for_QID = {} #mappes QIDs to (formula, num_of_occ), where num_of_occ is the number of occurrences for the formula that occurrs the most
    for (QID, formula), occ in formulae_dict.items():
        if most_common_formula_for_QID.get(QID) == None: #first formula for this QID will always be added
            most_common_formula_for_QID[QID] = (formula, occ)
        elif most_common_formula_for_QID[QID][1] < occ: #found a formula that occurrs more often
            most_common_formula_for_QID[QID] = (formula, occ)
    if args.verbosity_level > 0:
        print("Most common formulae (QID, formula, #occurences):")
        print(most_common_formula_for_QID)
