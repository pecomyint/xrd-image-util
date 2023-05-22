# CHANGELOG

## [1.0.0] - 2023-05-22
First official release

## [0.5.0] - 2023-03-06

### Added
- Lazy loading for Scan class variables.
- RectROI class - Creates a rectangular region of interest that can present output from a series of scans.
- Line Data GUI: Monitor variable. If selected, y-axis variable will be divided by the monitor.
- Image Data GUI: Rectangular ROI's with controls.

##### Changed
- Line data GUI variable selector now holds list of all variables available in a catalog. Scans that do not include a selected variable name are blacked out and cannot be plotted.

## [0.4.0] - 2023-02-10
Basic GUI for viewing 1D Catalog data.

### Added
- Catalog.view_line_data(): A function that displays an interactive widget for viewing various 1D curves for all Scan variables in a given Catalog.


## [0.3.0] - 2023-01-30
Basic GUI for viewing Scan image data.

### Added
- Scan.view_image_data(): A function that displays an interactive widget for viewing orthogonal slices of a Scan object's image data, both raw and gridded.


## [0.2.0] - 2023-01-18
Basic Scan mapping and gridding.
### Added
- Catalog.list_scans(): A print function that returns metadata about every scan in a catalog
- Catalog.get_scan(scan_id): A scan retrieval function that uses a simple scan ID (rather than the UID) as a parameter
- Catalog.get_scans(scan_ids): A scan retrieval function that returns a list of scan objects
- The ability to create reciprocal space maps (RSM's) for 4-circle geometries. This step is completed automatically when a `Catalog` object is created.
- Scan.grid_data(...): A function that creates a gridded, interpolated, and transformed 3D image with respect to a scan's RSM.
### Changed
- Variables `bs_catalog` and `bs_run` have been renamed to `bluesky_catalog` and `bluesky_run`, respectively.
### Removed
- Various filtering functions in the Catalog class.


## [0.1.0] - 2023-01-04
First functional release. Provides users with a basic interface for accessing scans from a local catalog.
### Added
- The `Catalog` class, complete with functions to both filter and return scans from a local Bluesky catalog. This class also provides access to the raw Bluesky catalog through the `bs_catalog` class variable. 
- The `Scan` class, which provides easy-to-access metadata values and the raw Bluesky run (`bs_run`) associated with the scan.
### Notes
- v0.1.0 assumes that a catalog has already been unpacked and provided a name for local usage. The unpacking step will be addressed in future releases.
- A demo of v0.1.0's features can be found in the notebook `demos/xiu-demo-0-1-0.ipynb`.