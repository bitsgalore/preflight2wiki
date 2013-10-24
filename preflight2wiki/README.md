# preflight2wiki
Johan van der Knijff, KB/National Library of the Netherlands.

## What is *preflight2wiki*?
*Preflight2wiki* is a simple Python wrapper around *Apache Preflight*, the PDF/A-1 validator that is part of Apache [PDFBox](http://pdfbox.apache.org/). It takes a text file with URLs that point to PDF documents as input. Each PDF is subsequently downloaded, analysed with *Preflight* and the results are written as a table in either PHP Extra Markdown or Atlassian Confluence Wiki format. Output is sorted by error code. 

## Dependencies
Tested with Python 3.3 under MS Windows 7. Older Python versions probably won't work. *Java* is needed for running *Preflight* (a *JAR* of *Preflight* is included with this repo).

The *Preflight* *JAR* taken from:

[https://builds.apache.org/job/PDFBox-trunk/lastBuild/org.apache.pdfbox$preflight/](https://builds.apache.org/job/PDFBox-trunk/lastBuild/org.apache.pdfbox$preflight/)


## Licensing
*Preflight2wiki* is released under the [Apache 2.0 License](http://www.apache.org/licenses/LICENSE-2.0). *Apache PDFBox* is released under the [Apache 2.0 License](http://www.apache.org/licenses/LICENSE-2.0).

## Configuration
After installing  *preflight2wiki.py* open *config.xml* and update the *java* path.
<!--
Just unzip the contents of *jprofile_x.y.z_win32.zip* to any empty directory. Then open the configuration file ('*config.xml*') in a text editor and update the value of *java* to the location of *java* on your PC if needed.
-->

## Command-line syntax

    usage:  preflight2wiki.py fileIn outputMode

## Positional arguments

**fileIn**: plain text file with URLs of documents that need to be analysed  

**outputMode**: select 'markdown' or 'confluence'

Output is written to stdout.

## Input file example

This example illustrates the format of the input file:

    http://www.opf-labs.org/format-corpus/pdfCabinetOfHorrors/embedded_video_quicktime.pdf
    http://www.opf-labs.org/format-corpus/pdfCabinetOfHorrors/fileAttachment.pdf
    http://www.opf-labs.org/format-corpus/pdfCabinetOfHorrors/javascript.pdf


## Usage example

    preflight2wiki.py demoOPF.txt markdown > resultsDemoOPF.md

Note that *all* files that are referenced in the input file will be downloaded to the active working directory; also *Preflight* output files (in XML format) will be created there for each analysed file.

## Output format

|File|Apache Preflight Error(s)|
|:---|:---
|[embedded_video_quicktime.pdf](http://www.opf-labs.org/format-corpus/pdfCabinetOfHorrors/embedded_video_quicktime.pdf)|1.2.9: Body Syntax error, EmbeddedFile entry is present in a FileSpecification dictionary<br>1.4.6: Trailer Syntax error, ID is different in the first and the last trailer<br>5.2.1: Forbidden field in an annotation definition, The subtype isn't authorized : Screen<br>7.1.1: Error on MetaData, No type defined for {http://ns.adobe.com/xap/1.0/mm/}subject<br>
|[fileAttachment.pdf](http://www.opf-labs.org/format-corpus/pdfCabinetOfHorrors/fileAttachment.pdf)|1.2.9: Body Syntax error, EmbeddedFile entry is present in a FileSpecification dictionary<br>1.4.7: Trailer Syntax error, EmbeddedFile entry is present in the Names dictionary<br>7.1.1: Error on MetaData, No type defined for {http://ns.adobe.com/xap/1.0/mm/}subject<br>
|[javascript.pdf](http://www.opf-labs.org/format-corpus/pdfCabinetOfHorrors/javascript.pdf)|1.0: Syntax error, Error: Expected a long type, actual='n'<br>1.1: Body Syntax error, Second line must contains at least 4 bytes greater than 127<br>

## Limitations
I only created *preflight2wiki* to simplify my workflow in testing *Apache Preflight*, and I'm mainly using it for quickly creating simple reports. It hasn't had a lot of testing, and there are probably a lot of things that can go wrong. Output may also contain characters that mess up rendering of Markdown or Confluence. Use at your own risk!

