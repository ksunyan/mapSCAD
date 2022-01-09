# MapSCAD Project
Build 3D printable choropleth maps from GeoJSON data. 

The `jsonscad_builder.py` Python module provides programmers with methods for: 
* Reading geographic data from GeoJSON files
* Binding statistical data to geographical areas
* Adjusting 3D model parameters
* Writing OpenSCAD code to a `.scad` file

**Note:** This guide assumes that you are comfortable with Python syntax (especially Python lists) and that you have at least a basic understanding of 3D printing and computer-aided design (CAD) concepts.

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

### Overview of `example.py`
```python
import jsonscad_builder

bldr = jsonscad_builder.JsonScadBuilder()

bldr.read_json_file('County_Boundaries_of_NJ.geojson')
bldr.extract_features()

bldr.simplify()

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
This guide will explain the above `example.py` code. This guide will *not* provide a detailed description of all methods in the `JsonScadBuilder` class, nor will it include instructions on using OpenSCAD and slicer software to prepare the model for 3D printing.

For detailed information on `JsonScadBuilder` methods, see:
For a guide on the 3D printing process, see:

#### 1. Import the `json_scadbuilder` module and a create new `JsonScadBuilder` object
```python
import jsonscad_builder

bldr = jsonscad_builder.JsonScadBuilder()
```
In this example, the file `jsonscad_builder.py` is in the same directory as `example.py`. To create a new `JsonScadBuilder` object `bldr`, call the `JsonScadBuilder` class constructor. 

#### 2. Read GeoJSON data
```python
bldr.read_json_file('County_Boundaries_of_NJ.geojson')
```
In this example, the file `County_Boundaries_of_NJ.geojson` is in the same directory as `example.py`. The `read_json_file()` method takes as a parameter the path to the file containing GeoJSON data. If the method parses the file contents successfully, then the `bldr` object stores the data in an `OrderedDict`.

**Note:** The specified file can be any `.read()`-supporting text file or binary file containing a GeoJSON `FeatureCollection`; conventional file extensions are `.geojson` and `.json`. See [RFC 7946](https://datatracker.ietf.org/doc/html/rfc7946) for GeoJSON format standards. 

#### 3. Extract GeoJSON features
```python
bldr.extract_features()
```
You *must* call the `.extract_features()` function. `extract_features()` looks up the `'features'` array in the GeoJSON data `OrderedDict`. If the stored GeoJSON data is a `FeatureCollection`, the `extract_features()` will generate no error messages.   

#### 4. Simplify
```python
bldr.simplify()
``` 
To reduce the number of points in the final 3D model, call the `simplify()` method. This method uses the Ramer-Douglas-Peucker (RDP) Algorithm to calculate which points to preserve in the simplified geometries.  


#### 5. Bind statistical data to GeoJSON features
```python
bldr.bind_data_by_identifier('population', county_populations, 'COUNTY')
```

## Known Issues
OpenSCAD may occasionally generate the following error or warning messages:
* `WARNING: Object may not be a valid 2-manifold and may need repair!`
* `ERROR: The given mesh is not closed! Unable to convert to CGAL_Nef_Polyhedron.`
These messages indicate that the model contains one or more bad faces. I will need to determine whether this issue is due to the RDP Algorithm or other problems in the code.

## Acknowledgements
