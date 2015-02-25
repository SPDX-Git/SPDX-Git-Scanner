import sys
import Config
import os
import shutil
import time
import re
import zipfile

# Git API imports
import git.cmd
import git.remote
import git
from git.exc import GitCommandError

fileConfig = Config.Config()
fileConfig.ParseFile( 'config.txt' )

def DelDir( s ):
    if os.path.isdir( s ):
        if not os.name == 'nt': # Not a windows pc
            shutil.rmtree( s )
        else:
            os.system( 'rmdir /S /Q "' + s  + '"' ) # Windows has permission problems doing it the normal way

def MakeDirTree( s ):
    dirTree = s
    if os.path.sep in dirTree:
        dirTree = dirTree[ : dirTree.rfind( os.path.sep ) ]
    os.makedirs( dirTree )

def DoPrint( line, bVerbose ):
    if bVerbose:
        print( line )
    
def Main( config = fileConfig ):

    config.PrintConfig()

    bVerbose                = config.GetAsBool("Verbose")
    vBranch                 = config.Get("Branch")
    vTmpDir                 = config.Get("TmpDir")
    vTmpZip_Relative        = config.Get("TmpZip")
    vTmpZip_Absolute        = os.path.join( vTmpDir, vTmpZip_Relative )
    vSPDXFileName_Relative  = config.Get("SPDXOutput")
    vSPDXFileName_Absolute  = os.path.join( vTmpDir, vSPDXFileName_Relative )
    vCommitComment          = config.Get("CommitComment")
    vUser                   = config.Get("User")
    vPassword               = config.Get("Password")

    vCurrentOp              = ""

    try:
        
        # Set up temporary directory
        vCurrentOp = "Deleting old temporary directory if present"
        DoPrint( vCurrentOp, bVerbose )
        DelDir( vTmpDir )
        
        time.sleep(1)
        
        vCurrentOp      = "Making temporary directory"
        DoPrint( vCurrentOp, bVerbose )
        MakeDirTree( vSPDXFileName_Absolute )
        
        # Connect to Git
        vCurrentOp      = "Connecting to Git"
        DoPrint( vCurrentOp, bVerbose )
        vGitNtfc        = git.cmd.Git( vTmpDir )

        # Initiate a temporary repository
        vCurrentOp      = "Initiating temporary Git branch"
        DoPrint( vCurrentOp, bVerbose )
        vGitNtfc.init()

        # Pull the files down
        vCurrentOp      = "Pulling Git branch located at " + vBranch
        DoPrint( vCurrentOp, bVerbose )
        vGitNtfc.pull( vBranch )

        # Get all the file names
        vCurrentOp      = "Retrieving list of files from Git branch"
        DoPrint( vCurrentOp, bVerbose )
        vFileList       = vGitNtfc.ls_files().split("\n")

        # Create zip file
        vCurrentOp      = "Creating package file"
        DoPrint( vCurrentOp, bVerbose )
        vZipFile        = zipfile.ZipFile( vTmpZip_Absolute , 'w' )

        # Write SPDX Header
        vSPDXFile       = open( vSPDXFileName_Absolute, 'w' )                       # THIS WILL BE REMOVED
        vSPDXFile.write( "Hi, I'm the header generated on %s\n" % time.ctime() )    # THIS WILL BE REMOVED

        # Add files to package
        vCurrentOp      = "Processing files"
        DoPrint( vCurrentOp, bVerbose )
        if vSPDXFileName_Relative in vFileList: # Don't process the SPDX file
            vFileList.remove( vSPDXFileName_Relative )
        for vFile in vFileList:
            vSPDXFile.write( vFile + "\n" )                                         # THIS WILL BE REMOVED
            vZipFile.write( os.path.join( vTmpDir, vFile ), vFile )

        # Write SPDX tail
        vSPDXFile.write( "And I'm the tail\n" )                                     # THIS WILL BE REMOVED
        vSPDXFile.close()                                                           # THIS WILL BE REMOVED
        vZipFile.close()

        #
        # THIS IS WHERE I SHOULD BE DOING DOSOCS
        #

        # Remove the zip file
        vCurrentOp      = "Removing package file"
        DoPrint( vCurrentOp, bVerbose )
        os.remove( vTmpZip_Absolute )
        
        # Push SPDX to repository
        vCurrentOp      = "Adding SPDX file to local branch"
        DoPrint( vCurrentOp, bVerbose )
        vGitNtfc.add( vSPDXFileName_Relative )

        vRepo = git.Repo( vTmpDir )
        if vRepo.is_dirty():
            vCurrentOp      = "Committing SPDX changes"
            DoPrint( vCurrentOp, bVerbose )
            vGitNtfc.commit( message=time.strftime( vCommitComment ) )
        
            vAuthString = ""
            if vUser:
                vAuthString = vUser + "@"
                if vPassword:
                    vAuthString = vPassword + vAuthString
            
            vPushTarg   = vBranch
            vCxnInfo    = re.findall( r"^(https?://)?(.*)", vPushTarg )
            if vCxnInfo:
                vProtocol, vURL = vCxnInfo[0]
                vPushTarg = vProtocol + vAuthString + vURL

            vCurrentOp      = "Connecting to remote repository"
            DoPrint( vCurrentOp, bVerbose )
            vRemote = git.remote.Remote( vRepo, vPushTarg )

            vCurrentOp      = "Pushing SPDX file to remote repository"
            DoPrint( vCurrentOp, bVerbose )
            vRemote.push()
        else:
            DoPrint( "SPDX Document is already up to date", bVerbose )
        
        # Delete local directory
        DelDir( vTmpDir )
    except GitCommandError as exc:
        print( '*'*30 )
        print( 'Error during "%s". Here\'s what was given to stderr:' % vCurrentOp )
        print( exc.stderr.decode('ascii') )
        print( '*'*30 )
    except Exception as exc:
        print( '*'*30 )
        print( 'Error during "%s". Here\'s the exception that was raised:' )
        raise exc

if __name__ == '__main__':
    args = sys.argv[1:]
    argc = len(args)

    commandLineConfig = fileConfig
    commandLineConfig.Parse( args )
    Main( commandLineConfig )
