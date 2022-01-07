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
OpenSCAD is open-source software for creating solid 3D CAD models. Since 3D modelling using OpenSCAD is purely script-based, the software is ideal for creating parametric 3D models. You can get OpenSCAD from the project's [Downloads page](https://openscad.org/downloads.html). 

See the [OpenSCAD User Manual](https://en.wikibooks.org/wiki/OpenSCAD_User_Manual) for more information.

### Slicer Software and STL Viewers
Since choice of slicer software for 3D printing largely depends on personal preference or compatibility with 3D printers, this guide will not address slicer software in detail. One popular slicer is [Ultimaker Cura](https://ultimaker.com/software/ultimaker-cura) (which was used in testing of this project). 

Software for viewing `.stl` files may also be helpful. Free STL viewers are widely available online for download. 

## Usage

## Known Issues

## Acknowledgements
