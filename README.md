# MapSCAD Project
Build 3D printable choropleth maps from GeoJSON data. 

The `jsonscad_builder.py` Python module provides programmers with methods for: 
* Reading geographic data from GeoJSON files
* Binding statistical data to geographical areas
* Adjusting 3D model parameters
* Writing OpenSCAD code to a `.scad` file

## Getting Started
Prior to using the `jsonscad_builder.py` module in your data visualization project, you will need to download and install some additional software.

### Python Dependencies
To simplify geometries, `jsonscad_builder.py` uses [an implementation of the Ramer-Douglas-Peucker Algorithm](https://github.com/fhirschmann/rdp). Install this module using `pip`:
```
pip install rdp
```
### OpenSCAD
OpenSCAD is open-source software for creating solid 3D CAD models. Since OpenSCAD modeling is purely script-based, the software is ideal for creating parametric 3D models. You can get OpenSCAD from the project's [Downloads page](https://openscad.org/downloads.html). 

See the [OpenSCAD User Manual](https://en.wikibooks.org/wiki/OpenSCAD_User_Manual) for more information.

### Slicer Software and STL Viewers
Since choice of slicer software for 3D printing largely depends on personal preference or compatibility with 3D printers, this guide will not address slicer software in detail. One popular slicer is [Ultimaker Cura](https://ultimaker.com/software/ultimaker-cura) (which was used in testing of this project). 

Software for viewing `.stl` files may also be helpful. Free STL viewers are widely available online for download. 

## Example Code

### Overview
```python
import jsonscad_builder

bldr = jsonscad_builder.JsonScadBuilder()

bldr.read_json_file('County_Boundaries_of_NJ.geojson')
bldr.extract_features()

county_populations = [
		['ATLANTIC', 274534], ['BERGEN', 955732], ['BURLINGTON', 461860],
		['CAMDEN', 523485], ['CAPE MAY', 95263], ['CUMBERLAND', 154152],
		['ESSEX', 863728], ['GLOUCESTER', 302294], ['HUDSON', 724854],
		['HUNTERDON', 128947], ['MERCER', 387340], ['MIDDLESEX', 863162],
		['MONMOUTH', 643615], ['MORRIS', 509285], ['OCEAN', 637229],
		['PASSAIC', 524118], ['SALEM', 64837], ['SOMERSET', 345361],
		['SUSSEX', 144221], ['UNION', 575345], ['WARREN', 109632]
	]

bldr.bind_data_by_identifier('population', county_populations, 'COUNTY')
bldr.transform([-76.0, 38.6], 50, 1)
bldr.scale_heights([60000, 1000000],[3,12])
bldr.write_scad_file('nj_populations.scad')
```
### Step-by-Step Guide
#### 1. Import `json_scadbuilder` module and create new object
```python
import jsonscad_builder

bldr = jsonscad_builder.JsonScadBuilder()
```

#### 2. Read GeoJSON data
```python
bldr.read_json_file('County_Boundaries_of_NJ.geojson')
```

#### 3. Extract GeoJSON features
```python
bldr.extract_features()
```

#### 4. Bind statistical data to GeoJSON features
```python
bldr.bind_data_by_identifier('population', county_populations, 'COUNTY')
```

## Known Issues

## Acknowledgements
