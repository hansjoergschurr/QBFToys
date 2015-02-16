#!/usr/bin/python
# Converts a folder containing .qdimacs problems into thf problems.

import argparse
import os
import os.path
import csv
import sys
from subprocess import PIPE, check_output, CalledProcessError

class PreprocessorError(Exception):
    pass
class ConverterError(Exception):
    pass

def convert(infile, outfileName, command):
    cmdString = "{} | ./converter -o {}; echo ${{PIPESTATUS[0]}} ${{PIPESTATUS[1]}}"
    command = cmdString.format(command, outfileName)
    h = check_output(command, executable="/bin/bash", shell=True, stdin=infile)
    h=h.split()
    returnCode1 = h[-2]
    returnCode2 = h[-1]
    if not returnCode2 == "0":
        raise ConverterError()
    if not (returnCode1 == "0" or returnCode1 == "10" or returnCode1 == "20"): 
        raise PreprocessorError() 
    statusFlag = "n"
    if len(h)==6:
        statusFlag = "s"
    return (int(h[0]), int(h[1]), statusFlag) 

parser = argparse.ArgumentParser(description='Recursively converts .qdimacs problems into thf problems.')
parser.add_argument('input',type=str,
    help='the folder containing the problems.')
parser.add_argument('output',type=str,
    help='the target folder.')
parser.add_argument("-r", "--results", type=str, help="name for csv file containing the results.",
    default="results.csv")
parser.add_argument("-p","--preprocessors", help="CSV file containing the preprocessor commands.",
    type=str, default="preprocessors.csv")
args = parser.parse_args()

if not os.path.exists(args.output):
    os.makedirs(args.output)

preprocessors = []
# Read prprocessor description
try:
    with open(args.preprocessors, 'rb') as csvFile:
        preprocessorReader = csv.reader(csvFile, delimiter=';')
        preprocessorReader.next() #skip header
        preprocessors=map(lambda x:x[1], preprocessorReader)
except IndexError:
    print "Not enough columngs in preprocessor decleration."
    sys.exit(1)

preprocessors.insert(0,"cat")

for i in xrange(len(preprocessors)):
    path = os.path.join(args.output,str(i))
    if not os.path.exists(path):
        os.makedirs(path)
with open(args.results,"wb") as resultsFile:
    results = csv.writer(resultsFile, delimiter=";")
    for root, dirs, files in os.walk(args.input):
        for file in files:
            fileName, fileExtension = os.path.splitext(file)	
            if fileExtension == ".qdimacs":
                print "\nConverting: {0}:".format(fileName)
                f = open(os.path.join(root,file),"r")

                row = [file]
                for i in xrange(len(preprocessors)):
                    outpath = os.path.join(args.output,str(i),fileName+".thf")
                    try:
                        (variables,clauses,statusFlag) = convert(f,outpath,preprocessors[i])
                        row.extend([variables, clauses, statusFlag])
                        print "{},{},{}".format(variables,clauses,statusFlag),
                    except OSError:
                        print "[Error exec.:{}]".format(preprocessors[i])
                        row.extend([0, 0, "e"])
                    except ConverterError:
                        print "[Converter Error:{}]".format(preprocessors[i])
                        row.extend([0, 0, "e"])
                    except PreprocessorError:
                        print "[Preprocessor Error:{}]".format(preprocessors[i])
                        row.extend([0, 0, "e"])
                    f.seek(0)
                results.writerow(row)
