#!/usr/bin/env python
"""
/*******************************************************************************
   * Copyright (c) 2015 Hitachi India Pvt. Ltd.
  // Licensed under The GNU General Public License, version 2 (the "License");
  // you may not use this file except in compliance with the License.
  // You may obtain a copy of the License at
  //
  //    https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html
  //
  // Unless required by applicable law or agreed to in writing, software
  // distributed under the License is distributed on an "AS IS" BASIS,
  // WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  // See the License for the specific language governing permissions and
  // limitations under the License.
  * Contributors:
  * Hitachi India Pvt. Ltd. - script development, fixing bugs of implementation
*******************************************************************************/
"""

import os
import sys
import subprocess
from codecs import open

# print colored text according to message level
def display(message, level = 'info'):

    colorMap = {'err': 'red',
                'warn': 'yellow',
                'info': 'green'}

    coloredPrint(message, colorMap[level] if level in colorMap else 'white')


def coloredPrint(message, color = 'white', formatting = 'bold'):

    formatCode = {'bold': 1,
                  'bright': 1,
                  'dim': 2,
                  'underline': 4,
                  'reverse': 7,
                  'inverted': 7}

    colorCode = {'gray': 90,
                 'red': 91,
                 'green': 92,
                 'yellow': 93,
                 'blue': 94,
                 'magenta': 95,
                 'cyan': 96,
                 'white': 97}

    formatting = formatting.lower()
    color = color.lower()

    attributes = '\033[' + str(formatCode[formatting] if formatting in formatCode else 0) + ';' + \
                 str(colorCode[color] if color in colorCode else 97) + 'm'
    reset = '\033[0m'

    print(attributes + message + reset)


# when this script is called directly(not from make process) with one argument(filepath), display minimized statistics
def displaySummary(diffstat):

    totalFiles = 0
    changedFiles = 0
    originalLines = 0
    changedLines = 0

    if not (os.path.exists(diffstat) and sys.argv[1].endswith('diffstat.log')):
        display('Please specify diffstat.log file path.', 'warn')
        sys.exit(1)

    for line in open(diffstat, 'r'):
        if not line.split()[0].isdigit():
            continue

        for summary in line.split(','):
            if 'change' in summary:
                totalFiles = totalFiles + 1
                changedFiles = changedFiles + int(summary.split()[0])
            elif 'insertion' in summary:
                changedLines = changedLines - int(summary.split()[0])
            elif 'deletion' in summary:
                changedLines = changedLines + int(summary.split()[0])
            elif 'origin' in summary:
                originalLines = originalLines + int(summary.split()[0])

    display('%d out of %d compiled C files have been minimized.' % (changedFiles, totalFiles))
    display('Unused %d lines(%d%% of the original C code) have been removed.' % (changedLines, 100 * changedLines / originalLines))


# detect encoding for C file to open
def detectEncoding(filepath):

    if (os.system('file -i ' + filepath + ' > /dev/null 2>&1') >> 8) != 0:
        display('Failed to run file command.', 'err')
        display('Please install file utility in the host machine.', 'err')
        display('Suggestion: $ sudo apt-get install file', 'err')
        sys.exit(1)

    stdout = subprocess.Popen(['file', '-i', filepath], stdout=subprocess.PIPE).communicate()[0]

    # for Python 2.x and 3.x version compatibility
    encoding = (stdout if type(stdout) is str else stdout.decode()).strip().split('charset=')[-1]
    return encoding if '8859' in encoding else 'utf-8'


# True if the stripped line originated from the original line, False if they are different
def isCorrelatedLine(orgLine, strippedLine):

    correlated = True

    if strippedLine.strip().startswith('/*') and ''.join(strippedLine.split()) == ''.join(orgLine.split()):
        pass

    elif ''.join(strippedLine.split()) == ''.join(orgLine.split('/*')[0].split()):
        pass

    elif ''.join(strippedLine.split('//')[0].split()) == ''.join(orgLine.split('//')[0].split()):
        pass

    elif '/*' in orgLine and '*/' in orgLine and \
         ''.join(strippedLine.split()) == ''.join((orgLine.split('/*')[0] + orgLine.split('*/')[-1]).split()):
        pass

    elif not (orgLine.isspace() or orgLine.strip() == '\\') and \
         ''.join(orgLine.strip()[:-1].split()) in ''.join(strippedLine.split()) and \
         orgLine.strip().endswith('\\'):
        pass

    else:
        correlated = False

    return correlated


# True if the current original line corresponds to the stripped "TO BE REPLACED: " line, False if they don't match
def isCorrelatedIncludeLine(orgLine, headerPath):

    correlated = False

    incLine = ''.join(orgLine.split())
    if incLine.startswith('#include'):
        # 9 is len('#include') + 1
        correlated = headerPath.endswith(incLine[9: 9 + incLine[9:].find('>' if incLine[8] == '<' else '\"')])

    return correlated


# copy the relevant #include lines from the original C source file
def restoreHeaderInclude(mindir, target, strippedLines):

    detectedEncoding = detectEncoding(target)
    origin = open(target, 'r', encoding = detectedEncoding)
    minimized = open(mindir + target, 'w', encoding = detectedEncoding)

    for strippedLine in strippedLines:
        orgLine = origin.readline()

        # just copy if the preprocessed line is the same as the original line
        if orgLine == strippedLine:
            minimized.write(strippedLine)

        # skip writing extra blank lines
        elif strippedLine.isspace():
            continue

        # if valid contents found which is different from the original source
        else:

            # restore deleted #include sentence
            if strippedLine.startswith('TO BE REPLACED: '):
                # look for matching #include line in the original source file
                # strippedLine[17:-2] is the header path in the preprocessor output
                while not isCorrelatedIncludeLine(orgLine, strippedLine[17:-2]):
                    orgLine = origin.readline()
                    # if the matched #include line not found in the original source file, continue searching it from the first line
                    if orgLine == '':
                        origin.seek(0, 0)

                # write the original #include sentence, avoiding multi line /**/ comment
                minimized.write(orgLine.strip().split('/*')[0] + '\n' if ('/*' in orgLine and not '*/' in orgLine) else orgLine)

            # if not #include sentence and different line from the original, restore the original line
            else:
                # forward the original file until the corresponding line is found.
                while not isCorrelatedLine(orgLine, strippedLine):
                    orgLine = origin.readline()

                # write multiline macro definition as one line form
                if orgLine.strip().endswith('\\'):
                    minimized.write(strippedLine)

                # restore the original line, mostly it's #define sentence
                elif not '/*' in orgLine or orgLine.strip().startswith('/*') or '*/' in orgLine:
                    minimized.write(orgLine)
                # avoid multi line /**/ comment
                else:
                    minimized.write(orgLine.strip().split('/*')[0] + '\n')

    minimized.close()

    # write diff statistics for the minimization process
    if (os.system('diff -u ' + target + ' ' + mindir + target + ' >> ' + mindir + 'minimize.patch') >> 8) > 1 or \
       (os.system('diff -u ' + target + ' ' + mindir + target + '| diffstat -p 2 >> ' + mindir + 'diffstat.log') >> 8) != 0:
        display('Failed to run diff and diffstat commands.', 'err')
        display('Please install diff and diffstat utilities in the host machine.', 'err')
        display('Suggestion: $ sudo apt-get install diffutils diffstat', 'err')
        sys.exit(1)

    origin.seek(0, 0)
    os.system('echo \' ' + str(sum(1 for _ in origin)) + ' lines in the origin\' >> ' + mindir + 'diffstat.log')
    origin.close()


# identify and delete the expanded header file contents
def stripHeaders(mindir, target):

    preprocessed = open(mindir + target + '.preprocessed', 'r', encoding = detectEncoding(mindir + target + '.preprocessed'))
    strippedLines = []

    writeOn = False
    lastInclude = None
    for line in preprocessed:
        lineElements = line.split()

        # look for linemarkers from the Preprocessor Output in order to remove expanded header file contents
        if len(lineElements) >= 3 and line.startswith('# '):
            if lineElements[1].isdigit() and lineElements[2][0] == lineElements[2][-1] == '\"':
                # look for #include sentence to be restored in the original C file
                writeOn = True if lineElements[2][1:-1] == target else False

                # remember the header file name where its contents are removed
                if len(lineElements) >= 4:
                    if lineElements[3] == '2' and writeOn:
                        strippedLines.append('TO BE REPLACED: ' + lastInclude)

                lastInclude = lineElements[2] + '\n'
                continue

        # copy the line if it is not the header contents (copy only original C file contents)
        if writeOn:
            strippedLines.append(line)

    preprocessed.close()
    os.remove(mindir + target + '.preprocessed')

    return strippedLines


# perform gcc -E -fdirectives-only for the target C file
def preprocess(options):

    # delete sparse specific option that is contained in default CHECKFLAGS
    for unneccesaryOpt in ('-Wbitwise', '-D__STDC__', '-Wno-return-void'):
        if unneccesaryOpt in options:
            options.remove(unneccesaryOpt)

    # user's specified output directory if given
    if '-mindir' in options:
        i = options.index('-mindir')
        options.remove('-mindir')
        mindir = options.pop(i)
        mindir += '' if mindir.endswith('/') else '/'
    else:
        # default output directory
        mindir = '../minimized-tree/'

    # make up '"' in the -D option to avoid syntax error
    for i, v in enumerate(options):
        if '-D' in v:
            options[i] = v[:2] + '\"' + v[2:] + '\"'

    # construct preprocess command line
    minimizeCommand = ['gcc -E -fdirectives-only']
    minimizeCommand.extend(options)
    minimizeCommand = ' '.join(minimizeCommand)

    # target C source file with relative path
    target = options[-1]
    # relative output directory
    outdir = mindir + target[:target.rfind('/')]

    # prepare the output directory 
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # issue the minimized command
    if (os.system(minimizeCommand + ' > ' + mindir + target + '.preprocessed') >> 8) != 0:
        display('Failed to run the command:\n' + minimizeCommand, 'err')
        sys.exit(1)

    return (mindir, target)


if __name__=="__main__":

    if len(sys.argv) == 1 or '-h' in sys.argv or '--help' in sys.argv:
        display('please use Makefile in the source tree.\nusage:', 'warn')
        display(' export PATH=$PATH:`pwd`', 'warn')
        display(' make C=1 CHECK=minimize.py CF=\"-mindir ../minimized-tree/\"\n', 'warn')
        display('use C=1 to perform minimization only for (re)compilation target files.', 'warn')
        display('use C=2 to perform minimization for all the source files regardless of whether they are compilation target or not.', 'warn')
        display('C, CHECK flags are mandatory. -mindir option in CF flag is optional, the default minimized tree location is \"../minimized-tree\"\n', 'warn')
        sys.exit(0)

    # when this script is called directly(not from make process) with one argument(filepath), display minimized statistics
    elif len(sys.argv) == 2:
        displaySummary(sys.argv[1])
        sys.exit(0)

    # run preprocess cpmmand with options passed through Makefile
    mindir, target = preprocess(sys.argv[1:])

    # remove expanded header file contents
    restoreHeaderInclude(mindir, target, stripHeaders(mindir, target))
