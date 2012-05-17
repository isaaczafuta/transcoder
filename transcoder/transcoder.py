import pyflacmeta
import os
import os.path
import stagger
import subprocess

class Transcoder:
    def __init__(self, flacpath, mp3path):
        self.flacpath = os.path.expanduser(flacpath)
        self.mp3path = os.path.expanduser(mp3path)
        
    def getmp3path(self, path):
        relpath = os.path.relpath(path, self.flacpath)
        if os.path.splitext(relpath)[1] == ".flac":
            relpath = ".".join([os.path.splitext(relpath)[0], "mp3"])
        return os.path.join(self.mp3path, relpath)
    
    def extensionsvalid(self, root, files):
        allowedextensions = set([".flac", ".log", ".cue", ".jpg"])
        extensions = set((os.path.splitext(file)[1] for file in files))
        if extensions != allowedextensions:
            return False
        return True
        
    def getdepth(self, root):
        return root.count(os.sep) - self.flacpath.count(os.sep)
        
    def filedepthvalid(self, root):
        parentfolder = os.path.split(root)[1]
        if self.getdepth(root) == 2:
            return True
        elif self.getdepth(root) == 3 and parentfolder[0:5] == "Disc ":
            return True
        return False
        
    def metadatacorrect(self, flacfile):
        tags = self.get_tags(flacfile)
        tagdict = tags.tags()
        required_tags = set(["artist", "album", "title", "date", 
                             "tracknumber", "tracktotal", "discnumber",
                            "disctotal"])
        present_tags = set([key.lower() for key in tagdict.keys()])
        if required_tags - present_tags:
            return False
        flacfilename = os.path.basename(flacfile)
        title = tags["TITLE"].replace("/", "-")
        tracknumber = "%02d" % int(tags["TRACKNUMBER"])
        properfilename = tracknumber + " " + title + ".flac"
        if flacfilename != properfilename:
            return False
        return True
        
    def get_tags(self, flacfile):
        audio = pyflacmeta.FLAC(flacfile)
        return audio
        
    def tag_mp3(self, mp3file, tags, artpath):
        pass
        tag = stagger.read_tag(mp3file)
        tag.artist = tags["ARTIST"]
        tag.album = tags["ALBUM"]
        tag.title = tags["TITLE"]
        tag.track = tags["TRACKNUMBER"]
        tag.track_total = tags["TRACKTOTAL"]
        tag.disc = tags["DISCNUMBER"]
        tag.disc_total = tags["DISCTOTAL"]
        tag.date = tags["DATE"]
        tag.picture = artpath
        tag.write()
        
    def transcodefile(self, flacfile, mp3file):
        print("Transcoding", flacfile)
        flaccommand = ["flac", "-s", "-c", "-d", flacfile]
        lamecommand = ["lame", "--silent", "--add-id3v2", "-V", "2", "-", mp3file]
        p1 = subprocess.Popen(flaccommand, stdout=subprocess.PIPE)
        p2 = subprocess.Popen(lamecommand, stdin=p1.stdout)
        p1.stdout.close()
        p2.communicate()
        folderpath = os.path.dirname(flacfile)
        artname = os.path.basename(folderpath) + ".jpg"
        artpath = os.path.join(folderpath, artname)
        tags = self.get_tags(flacfile)
        self.tag_mp3(mp3file, tags, artpath)

    def transcode(self):
        for (root, dirs, files) in os.walk(self.flacpath):
            if files and dirs and files != [".DS_Store"]:
                print("Unwanted files in", root)
                break
            elif dirs:
                mp3root = self.getmp3path(root)
                for dir in dirs:
                    mp3dir = os.path.join(mp3root, dir)
                    if not os.path.exists(mp3dir):
                        os.mkdir(mp3dir)
            elif files:
                if not self.filedepthvalid(root):
                    print("Files at incorrect level in", root)
                    continue
                if not self.extensionsvalid(root, files):
                    print("Missing or incorrect file extensions in", root)
                    continue
                for file in files:
                    extension = os.path.splitext(file)[1]
                    if extension == ".flac":
                        flacfile = os.path.join(root, file)
                        mp3file = self.getmp3path(flacfile)
                        if os.path.isfile(mp3file):
                            if os.path.getmtime(mp3file) > os.path.getmtime(flacfile):
                                continue
                        if not self.metadatacorrect(flacfile):
                            print("Incorrect metadata in", flacfile)
                            continue
                        self.transcodefile(flacfile, mp3file)
