#!/usr/bin/python
import os
import re
import urllib2
import bz2

def get_QID(title, title_language="en"):
    def get_html_code(title, title_language):
        '''returns html code from "https://" + title_language + ".wikipedia.org/w/api.php?action=query&prop=pageprops&format=json&titles=" + title'''
        def open_url(url):
            try:
                req = urllib2.Request(url)
                http_response_object = urllib2.urlopen(req)
                return http_response_object
            except Exception as e:
                print("Error with url: " + url)
                print(e)
                print()

        url = 'https://' + title_language + '.wikipedia.org/w/api.php?action=query&prop=pageprops&format=json&titles=' + title

        http_response_object = open_url(url)
        html_as_bytes = http_response_object.read() #type: bytes
        html = html_as_bytes.decode("utf8") #type: str

        return html

    title = title.replace(" ", "%20") #anything else to replace for html in this url-part?

    html = get_html_code(title, title_language)
    html = html.split("\n")

    for line in html:
        QID = re.search('\"wikibase_item\":\"(Q[0-9]*)\"', line)
        if QID != None: #match found
            QID = QID.group(1)
            print(QID)
    return QID

def convert_titles_from_file_to_QIDs(filename):
    '''Works for txt-files where each line only contains
    <title>SOME-TITLE</title>
    or
    SOME-FORMULA-BUT-NO-TITLE
    No mixed line of title and formula is allowed.'''

    lines_to_be_written = [] #same as input but with QIDs instead of titles

    #read file and change titles -> QIDs
    file = open(filename, "r")
    lines = file.readlines()
    for line in lines:
        title = re.search("<title>(.*)</title>", line)
        if title != None: #line with title
            lines_to_be_written.append(get_QID(title.group(1)) + "\n")
        else: #line with formula
            lines_to_be_written.append(line)
    file.close()

    #write file
    file = open(filename, "w")
    lines_to_be_written = "".join(lines_to_be_written)
    file.write(lines_to_be_written)

    file.close()

if __name__ == '__main__':  # When the script is self run
    convert_titles_from_file_to_QIDs("Gold Standard.txt")
