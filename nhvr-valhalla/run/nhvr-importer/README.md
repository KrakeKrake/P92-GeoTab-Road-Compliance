# NHVR Importer
This is an importer for NHVR provided GeoPackages

> Note that as of writing, the geopackages that NHVR supplies are **NOT** officially certified to be used for routing.



## How to use
### 1. Gather Data
Gather the NHVR networks in geopackage form (potentially requires each network in a seperate geopackage, the naming of the geopackages does not matter)

Please also prepare an osm.pbf file, this is where the map data will be drawn from and place it in the osm.pbf folder.
Note that there should only be one of these.

The importer matches OSM-IDs

### 2. Create Virtual Environment
To ensure everything is installed properly, first create the virtual environment (if not already)
```python
python -m venv venv
```
Source it:
```python
source venv/bin/activate
```
Install the required packages:
```python
pip install -r requirements.txt
```

### 3. Run the following
Run the following with your values:
```python
python import-nhvr.py --nhvr-dir <nhvr-dir> --input <input osm.pbf> --output <output osm.pbf>
```
Where:
- \<nhvr-dir> is the directory containing the NHVR geopackages
- \<input osm.pbf> is the base osm.pbf
- \<output osm.pbf> is the outputted osm.pbf
Example:
```python
python import-nhvr.py --nhvr-dir nhvr/ --input osm.pbf/victoria-260907.osm.pbf --output victoria.nhvr.osm.pbf
```