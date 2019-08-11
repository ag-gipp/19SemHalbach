# 19SemHalbach
Research task: Find most common formulae across Wikipedia pages that are available in different languages.

Goal: Extract defining formula from Wikipedia pages more often than by extracting the first formula on a Wikipedia page.

Use wikiFilter.py to filter wikidumps of different languages for all pages that contain a tag(e.g. math-tag), found in "Dumps filtered for tags". Those can then be further filtered via wikiFilter.py for all pages belonging to a QID(given via --QID_file, use "Gold Standard.txt"), found in "Dumps filtered for tags/filtered 100 QIDs".
These filtered results can then easily be used to extract small bz2-files via find_most_common_formula.py for all languages containing the titles(corresponding to the given QIDs) together with all formulae from said pages. These are then used to find the most common formula from a page across its different languages.

To use other languages, download the original, big Dumps via the links given in "links to dumps.txt" and use wikiFilter.py to get the filtered dumps in "Dumps filtered for tags".
Due to the maximum file size on GitHub, the filtered results for multiple languages are not uploaded to "Dumps filtered for tags", but the further filtered results are included in "Dumps filtered for tags/filtered 100 QIDs".

In the folder miscellaneous, files useful during the development of the project are included for the sake of completeness.