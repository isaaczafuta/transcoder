transcoder
==========

This project is a simple python script to keep an MP3 mirror of a FLAC library.

Example usage:

::

    >>> import transcoder
    >>> transcoder = transcoder.Transcoder("~/Desktop/FLAC", "~/Desktop/MP3")
    >>> transcoder.transcode()
