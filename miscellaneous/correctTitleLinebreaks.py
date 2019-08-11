#Program to correct title linebreaks that occured due to a now solved bug in find_most_common_formula.py
#!/usr/bin/python
import os
import bz2

ifilenames = []
for root, directories, filenames in os.walk("./"):
    for filename in filenames:
        if filename.endswith(".bz2"):
            ifilenames.append(filename)
    break
print("ifilenames: " + str(ifilenames))

for ifilename in ifilenames:
    ifile = bz2.BZ2File(ifilename, 'r')
    ofile = bz2.BZ2File(ifilename.split(".bz2")[0] + "correctedTitleLinebreaks" + ".bz2", 'w')
    lines_to_be_written = []

    last_line_included_title = False
    for line in ifile:
        if line.find("<title>") != -1:
            if (line.find("<title>") == 0) and (last_line_included_title == True):
                lines_to_be_written.append("\n") #add empty line, since there was no formula found for the last title
                lines_to_be_written.append(line)
            elif (line.find("<title>") > 0) and (last_line_included_title == True):
                print("ERROR 1! Unexpected case occured! In line:")
                print(line)
            elif line.find("<title>") > 0:
                lines_to_be_written.append(line[0:line.find("<title>")] + "\n") #add linebreak before title
                lines_to_be_written.append(line[line.find("<title>") : len(line)].replace("\n", "") + "\n")
            elif line.find("<title>") == 0:
                lines_to_be_written.append(line)
            else:
                print("ERROR 2! Unexpected case occured! In line:")
                print(line)

            last_line_included_title = True
        else:
            last_line_included_title = False
            lines_to_be_written.append(line.replace("\n", "") + "\n")
        print( '"' + line + '"')
        print(last_line_included_title)
    if last_line_included_title == True:
        lines_to_be_written.append("\n\n") #add empty line for title in last line, in case it doesn't have a formula
    ifile.close()

    #write to output
    lines_to_be_written = "".join(lines_to_be_written).replace("</mediawiki>", "")
    ofile.write(lines_to_be_written)
    ofile.close()
