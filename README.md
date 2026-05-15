# ShareSweeper
*by Matteo Iacovantuono*

## Overview

ShareSweeper is a Python tool for recursively enumerating SMB shares during penetration testing engagements. While working through lab and CTF environments, I often found myself manually navigating shares with `smbclient`, making it difficult to keep track of interesting files and their location within the directory structure. ShareSweeper was built to address this, automating the process and providing a variety of options to streamline SMB share enumeration.

## Installation

Clone the repository:

```
git clone https://github.com/matteo-iacovantuono/sharesweeper.git
```

Install dependencies:

```
pip install -r requirements.txt
```
Run ShareSweeper:

```
python3 sharesweeper.py --help
```

## Disclaimer

This tool is intended for educational use and authorised penetration testing only. Unauthorised use against systems without explicit permission is strictly prohibited.

## Features

- Recursively enumerates all accessible files and directories in an SMB share, producing a structured file tree.
- Automatically flags interesting files by file extension and keywords.
- Supports both credentialed and anonymous authentication.
- Optional automatic download of flagged files.
- Supports custom file extension and keyword lists.
- Optionally save tool output to a text file for offline review.

## Command-line Options

### Required Arguments

```
-H              Target IP or hostname
-s              Share name to enumerate
```

### Optional Arguments

```
-u              Username (default: blank)
-p              Password (default: blank)
-d              Target domain
--ext-file      Path to file containing additional interesting extensions (one per line)
--kw-file       Path to file containing additional interesting keywords (one per line)
--download      Automatically download flagged files
--loot-dir      Directory to save downloaded files (default: ./loot/)
--output        File to save tool output to (e.g. output.txt)  
```

## Usage

**Basic Authenticated Enumeration**

```
python3 sharesweeper.py -H <target> -u <username> -p <password> -s <share>
```
**Anonymous Authentication**

```
python3 sharesweeper.py -H <target> -s <share>
```

**Automatically Download Flagged Files**

```
python3 sharesweeper.py -H <target> -u <username> -p <password> -s <share> --download
```

**Using Custom Extension and Keyword Lists**

```
python3 sharesweeper.py -H <target> -u <username> -p <password> -s <share> --ext-file <file> --kw-file <file>
```

Example lists are provided in `examples/` as a starting point.


**Save Output to a Text File**

```
python3 sharesweeper.py -H <target> -u <username> -p <password> -s <share> --output <file>
```

## To-Do

- [ ] Add support for Pass the Hash authentication
- [ ] Implement option to automatically enumerate all available shares on a target
- [ ] Support multiple targets via an input file
- [ ] Add filtering options (e.g. skip empty files, exclude specific directories)
