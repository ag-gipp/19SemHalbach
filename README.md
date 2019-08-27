# most-common-formula-across-wikipedia-languages
Research task: Find most common formulae across Wikipedia pages that are available in different languages.

Goal: Extract defining formula from Wikipedia pages more often than by extracting the first formula on a Wikipedia page.


Use wikiFilter.py to filter wikidumps of different languages for all pages that contain a tag (e.g. math-tag), found in "Dumps filtered for tags". Those can then be further filtered via wikiFilter.py for pages belonging to certain QIDs (given via --QID_file, use "Gold Standard.txt"), found in "Dumps filtered for tags/filtered 100 QIDs".
Use wikiFilter.py as follows:
```
usage: wikiFilter.py [-h] [-f [FILENAMES [FILENAMES ...]]] [-s SIZE] [-d DIR]
                     [-t [TAGS [TAGS ...]]] [-k [KEYWORDS [KEYWORDS ...]]]
                     [-K KEYWORD_FILE] [-Q QID_FILE] [-v] [-T]

Extract wikipages that contain the math tag.

optional arguments:
  -h, --help            show this help message and exit
  -f [FILENAMES [FILENAMES ...]], --filename [FILENAMES [FILENAMES ...]]
                        The bz2-file(s) to be split and filtered. You may use
                        one/multiple file(s) or e.g. "*.bz2" as input.
                        (default: enwiki-latest-pages-articles.xml.bz2)
  -s SIZE, --splitsize SIZE
                        The number of pages contained in each split. (default:
                        1000000)
  -d DIR, --outputdir DIR
                        The directory name where the files go. (default: wout)
  -t [TAGS [TAGS ...]], --tagname [TAGS [TAGS ...]]
                        Tags to search for, e.g. use -t TAG1 TAG2 TAG3
                        (default: ['math', 'ce', 'chem', 'math chem'])
  -k [KEYWORDS [KEYWORDS ...]], --keyword [KEYWORDS [KEYWORDS ...]]
                        Keywords to search for, e.g. use -k KEYWORD1 KEYWORD2
                        KEYWORD3 You might want to disable tags = specify
                        empty tags (""), if you don`t want pages containing a
                        tag OR a keyword! (default: [])
  -K KEYWORD_FILE, --keyword_file KEYWORD_FILE
                        Another way to specify keywords. Use a keyword file
                        containing one keyword (e.g.
                        "<title>formulae</title>") in each line. (default: )
  -Q QID_FILE, --QID_file QID_FILE
                        QID-file, containing one QID (e.g. "Q1234") in each
                        line. They will be translated to the titles in their
                        respective languages and "<title>SOME_TITLE</title>"
                        will be used as keywords. Specify languages with "-l".
                        The languages will be taken from the beginning of the
                        filenames, which thus must start with
                        "enwiki"/"dewiki"/... for english/german/... !
                        (default: )
  -v, --verbosity
  -T, --template        Include all templates. (default: False)
```

These filtered results can then be used to quickly extract small bz2-files via find_most_common_formula.py for all languages containing the titles (corresponding to the given QIDs) together with all formulae from said pages. These are then automatically used to find the most common formula from a page across its different languages.
Use as follows:
```
usage: find_most_common_formula.py [-h] [-f [FILE [FILE ...]]] [-s SIZE]
                                   [-d DIR] [-Q QID_FILE] [-t TAGS] [-v] [-T]

Extract all formulae (defined as having a formula_indicator) from the
wikipages that contain the titles corresponding to the given QIDs(loaded via
"-Q"), in all specified languages(corresponding to the beginning of the
bz2-filenames, e.g. "enwiki....bz2"). Afterwards extracts the most common
formula for a wikipedia page (in all languages specified). Formulae occuring
multiple times for a wikipedia page(in a single language) are counted only
once!

optional arguments:
  -h, --help            show this help message and exit
  -f [FILE [FILE ...]], --filename [FILE [FILE ...]]
                        The bz2-file(s) to be filtered. Default: Use all
                        bz2-files in current folder. (default: )
  -s SIZE, --splitsize SIZE
                        The number of pages contained in each split. (default:
                        1000000)
  -d DIR, --outputdir DIR
                        The output directory name. (default: wout)
  -Q QID_FILE, --QID_file QID_FILE
                        QID-file, containing one QID (e.g. "Q1234") in each
                        line(other lines without QIDs can be mixed in). They
                        will be translated to the titles in their respective
                        languages and "<title>SOME_TITLE</title>" will be used
                        as keywords. The languages will be taken from the
                        beginning of the filenames, which thus must start with
                        "enwiki"/"dewiki"/... for english/german/... !
                        "enwikibooks", "enwikiquote" etc. are not allowed!!!
                        (default: )
  -t TAGS, --tagname TAGS
                        Comma separated string of the tag names to search for;
                        no spaces allowed. (default: math,ce,chem,math chem)
  -v, --verbosity
  -T, --template        include all templates (default: False)
```

To use both wikiFilter.py as well as find_most_common_formula.py, they need to be in the same folder as the bz2-input-files.

To use other languages, download the original, big Dumps via the links given in "links to dumps.txt" and use wikiFilter.py to get the filtered dumps as in "Dumps filtered for tags".
Due to the maximum file size on GitHub, the filtered results for multiple languages are not uploaded to "Dumps filtered for tags", but the further filtered results are included in "Dumps filtered for tags/filtered 100 QIDs".

In the folder "miscellaneous", files useful during the development of the project are included for the sake of completeness.