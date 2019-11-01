# Importing KG2 into MediKanren

### Setup the enviroment

NOTE: This was tested on Ubuntu 18.04

To download and install everything you need to run kg2 into mediKanren simply run the `setup.sh` script on a unpriveliged user with passwordless sudo enabled like so:
```
bash -x ./setup.sh > setup.log 2>&1
```

Alternatively, if you are just trying to run mediKanren and not download and process a new graph you just need to install racket (and git if you do not have it) then run `git clone https://github.com/webyrd/mediKanren.git` to clone the mediKanren repository.

### Download the index files and run mediKanren.

Fist make sure that you have created the following directory in the mediKanren repository:
```
<path to repository>/mediKanren/biolink/data/rtx_kg2/
```

Next, download the indexes from [here](https://s3-us-west-2.amazonaws.com/rtx-kg2-public/kg2_indexes.tar.gz) and extract the files into the above mentioned `mediKanren/biolink/data/rtx_kg2` directory.

Then, navigate back to `/mediKanren/biolink` and make a copy of the `config.defaults.scm` named `config.scm` so that we don't edit `config.defaults.scm` as per the warning message at the top of the file.

In `config.scm` at the top there will be a few lines (starting at line 3) adding the databases:
```
((databases . (
               semmed
               orange
               robokop
               rtx
               ))
```
Add "rtx_kg2" under "rtx" so that this now becomes:
```
((databases . (
               semmed
               orange
               robokop
               rtx
               rtx_kg2
               ))
```

While still in `mediKanren/biolink` run the command `racket gui-simple-v2.rkt` (this may take a little time to load the graph into ram)
The gui should pop up after it loads everything.

### Downloading a new graph version

If you wish to download a new graph version a and generate the indexes from that then do the following:
1) Edit `config.yml` so that it has the correct url, username, and password for the kg2 instance you want to download.
2) run `setup.sh`
3) run `download-graph.sh`
4) run `create-index.sh` (This could take a few days and require between 64 and 128 GB of ram)
5) Follow the the avove steps starting from after downloading the indexes