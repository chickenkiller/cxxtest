#!/usr/bin/env python

import sys
from os.path import abspath, dirname
sys.path.insert(0, dirname(dirname(abspath(__file__))))
import re
import getopt
import glob
import string
from optparse import OptionParser
import cxxtest_parser
#import cxxtest_cxx
from cxxtest_misc import *

options = []
suites = []

def main():
    '''The main program'''
    global suites
    global options
    files = parseCommandline()
    #if options.new:
        #[options,suites] = cxxtest_cxx.scanInputFiles( files, options )
    #else:
    [options,suites] = cxxtest_parser.scanInputFiles( files, options )
    writeOutput()

def parseCommandline():
    '''Analyze command line arguments'''
    global options
    parser = OptionParser("%prog [options] [input_files]")
    #parser.add_option("--new",
    #                    action="store_true",
    #                    dest="new",
    #                    default=False,
    #                    help="Use new C++ parser"
    #                    )
    parser.add_option("-v", "--version",
                      action="store_true", dest="version", default=False,
                      help="Write CxxTest version")
    parser.add_option("-o", "--output",
                      dest="outputFileName", default=None, metavar="NAME",
                      help="Write output to file NAME")
    parser.add_option("", "--runner",
                      dest="runner", default="", metavar="CLASS",
                      help="Create a main() function that runs CxxTest::CLASS")
    parser.add_option("", "--gui",
                      dest="gui", metavar="CLASS",
                      help="Like --runner, with GUI component")
    parser.add_option("", "--error-printer",
                      action="store_true", dest="error_printer", default=False,
                      help="Same as --runner=ErrorPrinter")
    parser.add_option("", "--abort-on-fail",
                      action="store_true", dest="abortOnFail", default=False,
                      help="Abort tests on failed asserts (like xUnit)")
    parser.add_option("", "--have-std",
                      action="store_true", dest="haveStandardLibrary", default=False,
                      help="Use standard library (even if not found in tests)")
    parser.add_option("", "--no-std",
                      action="store_true", dest="noStandardLibrary", default=False,
                      help="Don't use standard library (even if found in tests)")
    parser.add_option("", "--have-eh",
                      action="store_true", dest="haveExceptionHandling", default=False,
                      help="Use exception handling (even if not found in tests)")
    parser.add_option("", "--no-eh",
                      action="store_true", dest="noExceptionHandling", default=False,
                      help="Don't use exception handling (even if found in tests)")
    parser.add_option("", "--longlong",
                      dest="longlong", default="long long", metavar="TYPE",
                      help="Use TYPE (default: long long) as long long")
    parser.add_option("", "--template",
                      dest="templateFileName", default=None, metavar="TEMPLATE",
                      help="Use TEMPLATE file to generate the test runner")
    parser.add_option("", "--include", action="append",
                      dest="headers", default=[], metavar="HEADER",
                      help="Include HEADER in test runner before other headers")
    parser.add_option("", "--root",
                      action="store_true", dest="root", default=False,
                      help="Write CxxTest globals")
    parser.add_option("", "--part",
                      action="store_true", dest="part", default=False,
                      help="Don't write CxxTest globals")
    parser.add_option("", "--no-static-init",
                      action="store_true", dest="noStaticInit", default=False,
                      help="Don\'t rely on static initialization")
    parser.add_option("", "--factor",
                      action="store_true", dest="factor", default=False,
                      help="Mystery option")

    (options, args) = parser.parse_args()

    if options.version:
      printVersion()

    if options.error_printer:
      options.runner= "ErrorPrinter"
      options.haveStandardLibrary = True

    if options.noStaticInit and (options.root or options.part):
        abort( '--no-static-init cannot be used with --root/--part' )

    if options.gui and not options.runner:
        options.runner = 'StdioPrinter'

    files = setFiles(args)
    if len(files) is 0 and not options.root:
        print parser.error("No input files found")
    return files


def printVersion():
    '''Print CxxTest version and exit'''
    sys.stdout.write( "This is CxxTest version INSERT_VERSION_HERE.\n" )
    sys.exit(0)

def setFiles(patterns ):
    '''Set input files specified on command line'''
    files = expandWildcards( patterns )
    return files

def expandWildcards( patterns ):
    '''Expand all wildcards in an array (glob)'''
    fileNames = []
    for pathName in patterns:
        patternFiles = glob.glob( pathName )
        for fileName in patternFiles:
            fileNames.append( fixBackslashes( fileName ) )
    return fileNames

def fixBackslashes( fileName ):
    '''Convert backslashes to slashes in file name'''
    return re.sub( r'\\', '/', fileName, 0 )


def writeOutput():
    '''Create output file'''
    if options.templateFileName:
        writeTemplateOutput()
    else:
        writeSimpleOutput()

def writeSimpleOutput():
    '''Create output not based on template'''
    output = startOutputFile()
    writePreamble( output )
    writeMain( output )
    if len(suites) > 0:
        print >>output, "bool "+suites[0]['name']+"_init = false;"
    writeWorld( output )
    output.close()

include_re = re.compile( r"\s*\#\s*include\s+<cxxtest/" )
preamble_re = re.compile( r"^\s*<CxxTest\s+preamble>\s*$" )
world_re = re.compile( r"^\s*<CxxTest\s+world>\s*$" )
def writeTemplateOutput():
    '''Create output based on template file'''
    template = open(options.templateFileName)
    output = startOutputFile()
    while 1:
        line = template.readline()
        if not line:
            break;
        if include_re.search( line ):
            writePreamble( output )
            output.write( line )
        elif preamble_re.search( line ):
            writePreamble( output )
        elif world_re.search( line ):
            writeWorld( output )
        else:
            output.write( line )
    template.close()
    output.close()

def startOutputFile():
    '''Create output file and write header'''
    if options.outputFileName is not None:
        output = open( options.outputFileName, 'w' )
    else:
        output = sys.stdout
    output.write( "/* Generated file, do not edit */\n\n" )
    return output

wrotePreamble = 0
def writePreamble( output ):
    '''Write the CxxTest header (#includes and #defines)'''
    global wrotePreamble
    if wrotePreamble: return
    output.write( "#ifndef CXXTEST_RUNNING\n" )
    output.write( "#define CXXTEST_RUNNING\n" )
    output.write( "#endif\n" )
    output.write( "\n" )
    if options.haveStandardLibrary:
        output.write( "#define _CXXTEST_HAVE_STD\n" )
    if options.haveExceptionHandling:
        output.write( "#define _CXXTEST_HAVE_EH\n" )
    if options.abortOnFail:
        output.write( "#define _CXXTEST_ABORT_TEST_ON_FAIL\n" )
    if options.longlong:
        output.write( "#define _CXXTEST_LONGLONG %s\n" % options.longlong )
    if options.factor:
        output.write( "#define _CXXTEST_FACTOR\n" )
    for header in options.headers:
        output.write( "#include \"%s\"\n" % header )
    output.write( "#include <cxxtest/TestListener.h>\n" )
    output.write( "#include <cxxtest/TestTracker.h>\n" )
    output.write( "#include <cxxtest/TestRunner.h>\n" )
    output.write( "#include <cxxtest/RealDescriptions.h>\n" )
    output.write( "#include <cxxtest/TestMain.h>\n" )
    if options.runner:
        output.write( "#include <cxxtest/%s.h>\n" % options.runner )
    if options.gui:
        output.write( "#include <cxxtest/%s.h>\n" % options.gui )
    output.write( "\n" )
    wrotePreamble = 1

def writeMain( output ):
    '''Write the main() function for the test runner'''
    if not (options.gui or options.runner):
       return
    output.write( 'int main( int argc, char *argv[] ) {\n' )
    if options.noStaticInit:
        output.write( ' CxxTest::initialize();\n' )
    if options.gui:
        tester_t = "CxxTest::GuiTuiRunner<CxxTest::%s, CxxTest::%s> " % (options.gui, options.runner)
    else:
        tester_t = "CxxTest::%s" % (options.runner)
    output.write( '    return CxxTest::Main<%s>( argc, argv );\n' % tester_t )
    output.write( '}\n' )

    #if options.gui:
        #output.write( 'int main( int argc, char *argv[] ) {\n' )
        #output.write( ' return CxxTest::GuiTuiRunner<CxxTest::%s, CxxTest::%s>( argc, argv ).run();\n' % (gui, runner) )
        #output.write( '}\n' )
    #elif options.runner:
        #output.write( 'int main() {\n' )
        #if options.noStaticInit:
            #output.write( ' CxxTest::initialize();\n' )
        #output.write( ' return CxxTest::%s().run();\n' % options.runner )

wroteWorld = 0
def writeWorld( output ):
    '''Write the world definitions'''
    global wroteWorld
    if wroteWorld: return
    writePreamble( output )
    writeSuites( output )
    if options.root or not options.part:
        writeRoot( output )
    if options.noStaticInit:
        writeInitialize( output )
    wroteWorld = 1

def writeSuites(output):
    '''Write all TestDescriptions and SuiteDescriptions'''
    for suite in suites:
        writeInclude( output, suite['file'] )
        if isGenerated(suite):
            generateSuite( output, suite )
        if isDynamic(suite):
            writeSuitePointer( output, suite )
        else:
            writeSuiteObject( output, suite )
        writeTestList( output, suite )
        writeSuiteDescription( output, suite )
        writeTestDescriptions( output, suite )

def isGenerated(suite):
    '''Checks whether a suite class should be created'''
    return suite['generated']

def isDynamic(suite):
    '''Checks whether a suite is dynamic'''
    return suite.has_key('create')

lastIncluded = ''
def writeInclude(output, file):
    '''Add #include "file" statement'''
    global lastIncluded
    if file == lastIncluded: return
    output.writelines( [ '#include "', file, '"\n\n' ] )
    lastIncluded = file

def generateSuite( output, suite ):
    '''Write a suite declared with CXXTEST_SUITE()'''
    output.write( 'class %s : public CxxTest::TestSuite {\n' % suite['name'] )
    output.write( 'public:\n' )
    for line in suite['lines']:
        output.write(line)
    output.write( '};\n\n' )

def writeSuitePointer( output, suite ):
    '''Create static suite pointer object for dynamic suites'''
    if options.noStaticInit:
        output.write( 'static %s *%s;\n\n' % (suite['name'], suite['object']) )
    else:
        output.write( 'static %s *%s = 0;\n\n' % (suite['name'], suite['object']) )

def writeSuiteObject( output, suite ):
    '''Create static suite object for non-dynamic suites'''
    output.writelines( [ "static ", suite['name'], " ", suite['object'], ";\n\n" ] )

def writeTestList( output, suite ):
    '''Write the head of the test linked list for a suite'''
    if options.noStaticInit:
        output.write( 'static CxxTest::List %s;\n' % suite['tlist'] )
    else:
        output.write( 'static CxxTest::List %s = { 0, 0 };\n' % suite['tlist'] )

def writeTestDescriptions( output, suite ):
    '''Write all test descriptions for a suite'''
    for test in suite['tests']:
        writeTestDescription( output, suite, test )

def writeTestDescription( output, suite, test ):
    '''Write test description object'''
    output.write( 'static class %s : public CxxTest::RealTestDescription {\n' % test['class'] )
    output.write( 'public:\n' )
    if not options.noStaticInit:
        output.write( ' %s() : CxxTest::RealTestDescription( %s, %s, %s, "%s" ) {}\n' %
                      (test['class'], suite['tlist'], suite['dobject'], test['line'], test['name']) )
    output.write( ' void runTest() { %s }\n' % runBody( suite, test ) )
    output.write( '} %s;\n\n' % test['object'] )

def runBody( suite, test ):
    '''Body of TestDescription::run()'''
    if isDynamic(suite): return dynamicRun( suite, test )
    else: return staticRun( suite, test )

def dynamicRun( suite, test ):
    '''Body of TestDescription::run() for test in a dynamic suite'''
    return 'if ( ' + suite['object'] + ' ) ' + suite['object'] + '->' + test['name'] + '();'
    
def staticRun( suite, test ):
    '''Body of TestDescription::run() for test in a non-dynamic suite'''
    return suite['object'] + '.' + test['name'] + '();'
    
def writeSuiteDescription( output, suite ):
    '''Write SuiteDescription object'''
    if isDynamic( suite ):
        writeDynamicDescription( output, suite )
    else:
        writeStaticDescription( output, suite )

def writeDynamicDescription( output, suite ):
    '''Write SuiteDescription for a dynamic suite'''
    output.write( 'CxxTest::DynamicSuiteDescription<%s> %s' % (suite['name'], suite['dobject']) )
    if not options.noStaticInit:
        output.write( '( %s, %s, "%s", %s, %s, %s, %s )' %
                      (suite['cfile'], suite['line'], suite['name'], suite['tlist'],
                       suite['object'], suite['create'], suite['destroy']) )
    output.write( ';\n\n' )

def writeStaticDescription( output, suite ):
    '''Write SuiteDescription for a static suite'''
    output.write( 'CxxTest::StaticSuiteDescription %s' % suite['dobject'] )
    if not options.noStaticInit:
        output.write( '( %s, %s, "%s", %s, %s )' %
                      (suite['cfile'], suite['line'], suite['name'], suite['object'], suite['tlist']) )
    output.write( ';\n\n' )

def writeRoot(output):
    '''Write static members of CxxTest classes'''
    output.write( '#include <cxxtest/Root.cpp>\n' )

def writeInitialize(output):
    '''Write CxxTest::initialize(), which replaces static initialization'''
    output.write( 'namespace CxxTest {\n' )
    output.write( ' void initialize()\n' )
    output.write( ' {\n' )
    for suite in suites:
        output.write( '  %s.initialize();\n' % suite['tlist'] )
        if isDynamic(suite):
            output.write( '  %s = 0;\n' % suite['object'] )
            output.write( '  %s.initialize( %s, %s, "%s", %s, %s, %s, %s );\n' %
                          (suite['dobject'], suite['cfile'], suite['line'], suite['name'],
                           suite['tlist'], suite['object'], suite['create'], suite['destroy']) )
        else:
            output.write( '  %s.initialize( %s, %s, "%s", %s, %s );\n' %
                          (suite['dobject'], suite['cfile'], suite['line'], suite['name'],
                           suite['object'], suite['tlist']) )

        for test in suite['tests']:
            output.write( '  %s.initialize( %s, %s, %s, "%s" );\n' %
                          (test['object'], suite['tlist'], suite['dobject'], test['line'], test['name']) )

    output.write( ' }\n' )
    output.write( '}\n' )

main()

#
# Copyright 2008 Sandia Corporation. Under the terms of Contract
# DE-AC04-94AL85000 with Sandia Corporation, the U.S. Government
# retains certain rights in this software.
#
